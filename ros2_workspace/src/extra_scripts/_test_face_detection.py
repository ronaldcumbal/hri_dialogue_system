# From: https://github.com/opencv/opencv_zoo/blob/main/models/face_detection_yunet/demo.py
# From YuNet: A Fast and Accurate CNN-based Face Detector (https://github.com/ShiqiYu/libfacedetection).')
# From: https://github.com/ros4hri/hri_face_detect/blob/humble-devel/hri_face_detect/node_face_detect.py
# This file is part of OpenCV Zoo project.
# It is subject to the license terms in the LICENSE file found in the same directory.
#
# Copyright (C) 2021, Shenzhen Institute of Artificial Intelligence and Robotics for Society, all rights reserved.
# Third party copyrights are property of their respective owners.

import os
import argparse
import random
import numpy as np
import cv2 as cv
from yunet import YuNet
from pathlib import Path

# Check OpenCV version
opencv_python_version = lambda str_version: tuple(map(int, (str_version.split("."))))
assert opencv_python_version(cv.__version__) >= opencv_python_version("4.10.0"), \
       "Please install latest opencv-python for benchmark: python3 -m pip install --upgrade opencv-python"

# Valid combinations of backends and targets
backend_target_pairs = [
    [cv.dnn.DNN_BACKEND_OPENCV, cv.dnn.DNN_TARGET_CPU],
    [cv.dnn.DNN_BACKEND_CUDA,   cv.dnn.DNN_TARGET_CUDA],
    [cv.dnn.DNN_BACKEND_CUDA,   cv.dnn.DNN_TARGET_CUDA_FP16],
    [cv.dnn.DNN_BACKEND_TIMVX,  cv.dnn.DNN_TARGET_NPU],
    [cv.dnn.DNN_BACKEND_CANN,   cv.dnn.DNN_TARGET_NPU]
]

def visualize(image, results, box_color=(0, 255, 0), text_color=(0, 0, 255), fps=None):
    output = image.copy()
    landmark_color = [
        (255,   0,   0), # right eye
        (  0,   0, 255), # left eye
        (  0, 255,   0), # nose tip
        (255,   0, 255), # right mouth corner
        (  0, 255, 255)  # left mouth corner
    ]

    if fps is not None:
        cv.putText(output, 'FPS: {:.2f}'.format(fps), (0, 15), cv.FONT_HERSHEY_SIMPLEX, 0.5, text_color)

    for det in results:
        bbox = det[0:4].astype(np.int32)
        cv.rectangle(output, (bbox[0], bbox[1]), (bbox[0]+bbox[2], bbox[1]+bbox[3]), box_color, 2)

        conf = det[-1]
        cv.putText(output, '{:.4f}'.format(conf), (bbox[0], bbox[1]+12), cv.FONT_HERSHEY_DUPLEX, 0.5, text_color)

        landmarks = det[4:14].astype(np.int32).reshape((5,2))
        for idx, landmark in enumerate(landmarks):
            cv.circle(output, landmark, 2, landmark_color[idx], 2)

    return output

if __name__ == '__main__':
    backend_id = backend_target_pairs[0][0]
    target_id = backend_target_pairs[0][1]

    # input str Usage: Set input to a certain image, omit if using camera.')
    parent_dir = Path(__file__).parent.parent
    model_path = os.path.join(parent_dir, 'models', 'yunet', 'face_detection_yunet_2023mar.onnx')
    conf_threshold = 0.9 # Minimum needed confidence for face detection, defauts to 0.9. Smaller values may result in faster detection, but will limit accuracy.
    nms_threshold = 0.3 # Suppress face bounding boxes of iou (Intersection over Union) >= nms_threshold. Default = 0.3. (if two boxes overlap by 30% or more, only the one with highest confidence is kept).
    top_k = 5000 # Usage: Keep top_k bounding boxes before NMS.')

    # Instantiate YuNet
    model = YuNet(modelPath=model_path,
                  inputSize=[640, 480], #320 320
                  confThreshold=conf_threshold,
                  nmsThreshold=nms_threshold,
                  topK=top_k,
                  backendId=backend_id,
                  targetId=target_id)


    # Use CLI to list all video devices: v4l2-ctl --list-devices 
    deviceId = 0
    cap = cv.VideoCapture(deviceId)
    w = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
    model.setInputSize([w, h])

    tm = cv.TickMeter()
    while cv.waitKey(1) < 0:
        hasFrame, frame = cap.read()

        if not hasFrame:
            print('No frames grabbed!')
            break       

        # Inference
        tm.start()
        faces = model.infer(frame) # results is a tuple
        tm.stop()

        # Draw results on the input image
        frame = visualize(frame, faces, fps=tm.getFPS())

        # Visualize results in a new Window
        cv.imshow('YuNet Demo', frame)

        tm.reset()
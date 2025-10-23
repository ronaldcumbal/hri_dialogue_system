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
from pkg_audio_input.yunet import YuNet
from pathlib import Path

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Header
from geometry_msgs.msg import TransformStamped, Vector3, Quaternion
from sensor_msgs.msg import CompressedImage, Image, CameraInfo

# from tf_transformations import quaternion_from_euler
# from tf2_geometry_msgs.tf2_geometry_msgs import Point, PointStamped
# from tf2_ros import Buffer, TransformBroadcaster, TransformListener

# from threading import Lock
# from typing import Dict, List, TypeAlias

# Check OpenCV version
opencv_python_version = lambda str_version: tuple(map(int, (str_version.split("."))))
assert opencv_python_version(cv.__version__) >= opencv_python_version("4.10.0"), \
       "Please install latest opencv-python for benchmark: python3 -m pip install --upgrade opencv-python"


class FaceDetectionNode(Node):

    def __init__(self):
        super().__init__('face_detection')

        self.create_subscription(Image, "/laptop_camera/image_raw", self.image_callback, 0)

        self.declare_parameter('devide_id', 0)
        self.deviceId = self.get_parameter('devide_id').value

        # YuNet configuration
        backend_target_pairs = [
            [cv.dnn.DNN_BACKEND_OPENCV, cv.dnn.DNN_TARGET_CPU],
            [cv.dnn.DNN_BACKEND_CUDA,   cv.dnn.DNN_TARGET_CUDA],
            [cv.dnn.DNN_BACKEND_CUDA,   cv.dnn.DNN_TARGET_CUDA_FP16],
            [cv.dnn.DNN_BACKEND_TIMVX,  cv.dnn.DNN_TARGET_NPU],
            [cv.dnn.DNN_BACKEND_CANN,   cv.dnn.DNN_TARGET_NPU]
        ]

        # MODELS_PATH = Path(__file__).parent.parent
        MODELS_PATH = '/home/roncu858/Github/hri_dialogue_system/ros2_workspace/src/pkg_audio_input/models'
        model_path = os.path.join(MODELS_PATH, 'yunet', 'face_detection_yunet_2023mar.onnx')
        conf_threshold = 0.9
        nms_threshold = 0.3 #if two boxes overlap by 30% or more, only the one with highest confidence is kept
        top_k = 5000 # Usage: Keep top_k bounding boxes before NMS.

        # Instantiate YuNet
        self.model = YuNet(modelPath=model_path,
                    inputSize=[640, 480], #320x320 is the default size
                    confThreshold=conf_threshold,
                    nmsThreshold=nms_threshold,
                    topK=top_k,
                    backendId=backend_target_pairs[0][0],
                    targetId=backend_target_pairs[0][1])

        # Add timer for camera processing
        self.tm = cv.TickMeter()
        self.timer = self.create_timer(0.033, self.timer_callback)  # ~30 FPS
        # self.cap = cv.VideoCapture(self.deviceId)

    #    # Get camera properties
    #     self.w = int(self.cap.get(cv.CAP_PROP_FRAME_WIDTH))
    #     self.h = int(self.cap.get(cv.CAP_PROP_FRAME_HEIGHT))
    #     self.model.setInputSize([self.w, self.h])
        self.get_logger().info('Face Detection Node has been started.')

    def image_callback(self, msg):
        """Callback function for image subscription"""

        self.get_logger().info('Received image frame.')

        # Convert ROS Image message to OpenCV image
        np_arr = np.frombuffer(msg.data, np.uint8)
        frame = cv.imdecode(np_arr, cv.IMREAD_COLOR)

        # Inference
        self.tm.start()
        faces = self.model.infer(frame)
        self.tm.stop()

        print(f"Detected {len(faces)} faces")

        # frame = self.visualize(frame, faces, fps=self.tm.getFPS())
        # cv.imshow('YuNet Demo', frame)
        # cv.waitKey(1)  # Required for OpenCV window updates

        self.tm.reset()

    def timer_callback(self):
        """Process camera frames at fixed intervals"""
        # hasFrame, frame = self.cap.read()
        # if not hasFrame:
        #     self.get_logger().warn('No frames grabbed!')
        #     return

        # # Inference
        # self.tm.start()
        # faces = self.model.infer(frame)
        # self.tm.stop()

        # print(f"Detected {len(faces)} faces")

        # frame = self.visualize(frame, faces, fps=self.tm.getFPS())
        # cv.imshow('YuNet Demo', frame)
        # cv.waitKey(1)  # Required for OpenCV window updates

        # self.tm.reset()

    def __del__(self):
        """Cleanup when node is destroyed"""
        self.cap.release()
        cv.destroyAllWindows()

    def visualize(self, image, results, box_color=(0, 255, 0), text_color=(0, 0, 255), fps=None):
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

def main(args=None):
    rclpy.init(args=args)
    node = FaceDetectionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
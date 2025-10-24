# From: https://github.com/opencv/opencv_zoo/blob/main/models/face_detection_yunet/demo.py
# From YuNet: A Fast and Accurate CNN-based Face Detector (https://github.com/ShiqiYu/libfacedetection).')
# From: https://github.com/ros4hri/hri_face_detect/blob/humble-devel/hri_face_detect/node_face_detect.py
# This file is part of OpenCV Zoo project.
# It is subject to the license terms in the LICENSE file found in the same directory.
#
# Copyright (C) 2021, Shenzhen Institute of Artificial Intelligence and Robotics for Society, all rights reserved.
# Third party copyrights are property of their respective owners.

import os
import random
import numpy as np
import cv2 as cv
from copy import deepcopy
from pkg_audio_input.yunet import YuNet
from pathlib import Path
from typing import Dict, List, TypeAlias
from dataclasses import asdict, astuple, dataclass, InitVar
from threading import Lock  

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Header
from geometry_msgs.msg import TransformStamped, Vector3, Quaternion
from sensor_msgs.msg import CompressedImage, Image, CameraInfo
from hri_msgs.msg import IdsList, NormalizedPointOfInterest2D, NormalizedRegionOfInterest2D
from rclpy.time import Time
from rclpy.qos import qos_profile_sensor_data
from cv_bridge import CvBridge

# Check OpenCV version
opencv_python_version = lambda str_version: tuple(map(int, (str_version.split("."))))
assert opencv_python_version(cv.__version__) >= opencv_python_version("4.10.0"), \
       "Please install latest opencv-python for benchmark: python3 -m pip install --upgrade opencv-python"

class Face:
    """
    This class is adapted from PAL Robotics S.L. ( Apache License, Version 2.0)
    Original source:
    https://github.com/ros4hri/hri_face_detect/blob/humble-devel/hri_face_detect/node_face_detect.py
    """
    last_id = 0

    def __init__(self, node: Node):
        # generate unique ID
        self.id = 'f%05d' % Face.last_id
        Face.last_id = (Face.last_id + 1) % 10000

        self.initial_detection_time: Time = None
        self.nb_frames_visible = 0
        self.nb_frames_since_last_detection = 0
        self.score = 0.

        # True once the publishers are initialised
        self.ready = False
        self.do_publish = False

    def initialise_publishers(self):
        """
        Initialise all the publishers for this face.

        Not done in the constructor as we typically wait for a few frames
        before publishing anything (to avoid creating too many spurious faces
        due to detection noise).
        """
        # already initialised?
        if self.ready:
            return

        ns = f'/humans/faces/{self.id}'
        self.roi_pub = self.node.create_publisher(NormalizedRegionOfInterest2D, ns + '/roi', 1)

        self.node.get_logger().info(f'New face: {self}')
        self.ready = True

    def publish(self, src_image, image_msg_header: Header):
        if not self.ready:
            self.node.get_logger().error(
                'Trying to publish face information but publishers have not been created yet!')
            return
        self.publish_normalized_roi(src_image, image_msg_header)

    def publish_normalized_roi(self, src_image: RGBMat, image_msg_header: Header):
        img_height, img_width, _ = src_image.shape
        msg = NormalizedRegionOfInterest2D()
        msg.header = image_msg_header
        msg.xmin, msg.ymin = pixel_to_normalized_coordinates(
            self.bb.xmin, self.bb.ymin, img_width, img_height)
        msg.xmax, msg.ymax = pixel_to_normalized_coordinates(
            self.bb.xmin + self.bb.width, self.bb.ymin + self.bb.height, img_width, img_height)
        msg.c = self.score
        self.roi_pub.publish(msg)

    def __del__(self):
        if not self.ready:
            return

        detect_time = (self.node.get_clock().now() - self.initial_detection_time).nanoseconds / 1e9
        self.node.get_logger().info(
            f'Face [{self}] lost. It remained visible for {detect_time:.2f}sec')

        self.node.destroy_publisher(self.roi_pub)
        self.ready = False

    def __repr__(self):
        return self.id

def bound(val, min_val, max_val):
    return max(min_val, min(val, max_val))

@dataclass
class FaceDetection:
    score: float
    def __post_init__(self):
        self.score = bound(self.score, 0., 1.)

class FaceDetector(Node):

    def __init__(self):
        super().__init__('face_detection')

        self.declare_parameter('devide_id', 0)
        conf_threshold = 0.9
        self.deviceId = self.get_parameter('devide_id').value

        MODELS_PATH = '/home/roncu858/Github/hri_dialogue_system/ros2_workspace/src/pkg_audio_input/models'
        model_path = os.path.join(MODELS_PATH, 'yunet', 'face_detection_yunet_2023mar.onnx')

        self.model = YuNet(modelPath=model_path,
                    inputSize=[640, 480], #320x320 is the default size
                    confThreshold=conf_threshold)

    def _extract_face_detection(raw_detection: List, scale: float, image_width: int, image_height: int) -> FaceDetection:
        score = float(raw_detection[0]) / 100.
        scaled_raw_coords = [int(x*scale) for x in raw_detection[1:15]]
        return FaceDetection(score)

    def detect(self, img) -> List[FaceDetection]:
        img_height, img_width, _ = img.shape

        # # Convert ROS Image message to OpenCV image
        # np_arr = np.frombuffer(msg.data, np.uint8)
        # frame = cv.imdecode(np_arr, cv.IMREAD_COLOR)

        # TODO: scale images if necessary
        raw_face_detections = self.model.infer(img)

        face_detections = [
            self._extract_face_detection(raw_face_detect, 1./self.image_scale, img_width, img_height)
            for raw_face_detect in raw_face_detections]
        valid_face_detections = [d for d in face_detections if d.score > self.confidence_threshold]

        return valid_face_detections


class FaceDetectionNode(Node):
    def __init__(self):
        super().__init__('face_detection')
        self.image_lock = Lock()
        self.proc_lock = Lock()  

        self.declare_parameters(
            namespace='',
            parameters=[
                ('processing_rate', 10.0),
                ('image_compressed', False),
                ('deterministic_ids', False),
                ('confidence_threshold', 0.9),
                ('image_scale', 1.0)
            ]
        )

        # Get parameter values
        self.processing_rate = self.get_parameter('processing_rate').value
        self.image_compressed = self.get_parameter('image_compressed').value
        self.deterministic_ids = self.get_parameter('deterministic_ids').value
        self.debug = self.get_parameter('debug').value

        # Initialize state variables
        self.image = None
        self.image_msg_header = None
        self.new_image = False
        self.skipped_images = 0
        self.last_id = 0
        self.knownFaces: Dict[str, Face] = dict()

        # Initialize timestamps
        self.start_skipping_ts = self.get_clock().now()
        self.detection_start_proc_time = self.get_clock().now()
        self.detection_proc_duration_ms = 0.

        # Create face detector
        self.face_detector = FaceDetector()

        # Create publishers
        self.faces_pub = self.create_publisher(
            IdsList, 
            '/humans/faces/tracked', 
            1
        )

        # Create subscribers
        self.image_info_sub = self.create_subscription(CameraInfo, 'camera_info', self.info_callback,
            qos_profile=qos_profile_sensor_data
        )
        # Create timer for image processing
        self.proc_timer = self.create_timer(1.0/self.processing_rate, self.process_image)

        # Set up image subscription based on compression parameter
        image_topic = 'image'  # Replace with your actual topic name
        if self.image_compressed:
            self.image_sub = self.create_subscription(
                CompressedImage,
                f'{image_topic}/compressed',
                self.image_callback,
                qos_profile=qos_profile_sensor_data
            )
        else:
            self.image_sub = self.create_subscription(
                Image,
                image_topic,
                self.image_callback,
                qos_profile=qos_profile_sensor_data
            )

        self.get_logger().info(
            f'Initialized face detection node. Listening on {self.image_sub.topic_name}'
        )

    def reset_faces(self):
        """Reset all tracked faces"""
        now = self.get_clock().now()
        self.knownFaces.clear()
        self.faces_pub.publish(IdsList(
            header=Header(stamp=now.to_msg()),
            ids=[]
        ))

    def info_callback(self, msg: CameraInfo):
        if not hasattr(self, 'msg'):
            self.msg = msg
            self.k = np.zeros((3, 3), np.float32)
            self.k[0][0:3] = self.msg.k[0:3]
            self.k[1][0:3] = self.msg.k[3:6]
            self.k[2][0:3] = self.msg.k[6:9]

    def image_callback(self, msg: Image | CompressedImage):
        with self.image_lock:
            if self.image_compressed:
                self.image = CvBridge().compressed_imgmsg_to_cv2(msg)
            else:
                self.image = CvBridge().imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.image_msg_header = msg.header

            if self.new_image:
                self.skipped_images += 1
                if self.skipped_images > 100:
                    now = self.get_clock().now()
                    skip_time = (now - self.start_skipping_ts).nanoseconds / 1e9
                    self.get_logger().warn(
                        "Face_detect's processing too slow. "
                        f'Skipped 100 new incoming image over the last {skip_time:.1f}sec')
                    self.start_skipping_ts = now
                    self.skipped_images = 0
            self.new_image = True

    def process_image(self):
        if (not self.new_image) or (not self.proc_lock.acquire(blocking=False)):
            return

        with self.image_lock:
            self.detection_start_proc_time = self.get_clock().now()
            image = deepcopy(self.image)
            image_msg_header = deepcopy(self.image_msg_header)
            self.new_image = False

        # copy the list of face ID before iterating over detection, so that we
        # can delete non-existant faces at the end.
        knownIds = list(self.knownFaces.keys())

        face_detections = self.face_detector.detect(image)

        self.proc_lock.release()

    def destroy_ros_interfaces(self):
        """Cleanup ROS interfaces"""
        self.destroy_timer(self.proc_timer)
        self.destroy_subscription(self.image_info_sub)
        self.destroy_subscription(self.image_sub)
        self.destroy_publisher(self.faces_pub)

def main(args=None):
    rclpy.init(args=args)
    node = FaceDetectionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
# From https://docs.opencv.org/4.10.0/dc/dbb/tutorial_py_calibration.html
import numpy as np
import argparse
import cv2
import os
import glob
import pickle

BASEPATH = os.path.dirname(__file__)

def capture_images(images_path, device_id = 0, min_images = 20):
    cap = cv2.VideoCapture(device_id)

    print("Press ESC to quit.")
    num=0
    while num <= min_images:
        ret, frame = cap.read()
        if not ret:
            print(f"Failed to grab frame from camera {device_id}")
        else:
            k = cv2.waitKey(100)
            if k == ord('s'):
                img_name = f"{num}.jpg"
                cv2.imwrite(os.path.join(images_path, img_name), frame)
                print(f"Image {img_name} saved")
                num += 1
            elif k == 27:    # Esc key to stop
                break
            cv2.imshow("Image", frame)

    cap.release()

def calibrate_camera(images_path, camera_name="camera", display=False):
    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    chess_size = (9,6) #<<<<<<<<<<----------- UPDATE

    objp = np.zeros((chess_size[0]*chess_size[1],3), np.float32)
    objp[:,:2] = np.mgrid[0:chess_size[0],0:chess_size[1]].T.reshape(-1,2)
    
    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.
 
    images = glob.glob(f'{images_path}/*.jpg')

    if not images:
        print("No images found!")
        return 0

    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, chess_size, None)
    
        # If found, add object points, image points (after refining them)
        if ret == True:
            objpoints.append(objp)
    
            corners2 = cv2.cornerSubPix(gray,corners, (11,11), (-1,-1), criteria)
            imgpoints.append(corners2)
    
            if display:
                # Draw and display the corners
                cv2.drawChessboardCorners(img, chess_size, corners2, ret)
                cv2.imshow('img', img)
                cv2.waitKey(500)
    
    cv2.destroyAllWindows()

    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

    camera_matrices_path = os.path.join(BASEPATH, f"{camera_name}_matrices.npz")
    np.savez(camera_matrices_path, mtx, dist, rvecs, tvecs)

    # Display matrices
    npzfile = np.load(camera_matrices_path)
    print("Arrays in file: ", npzfile.files)

    mtx_loaded = npzfile['arr_0']
    dist_loaded = npzfile['arr_1']
    rvecs_loaded = npzfile['arr_2']
    tvecs_loaded = npzfile['arr_3']

if __name__ == "__main__":

    image_folder = os.path.join(BASEPATH, "camera_images")

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--capture", action='store_true')
    args = parser.parse_args()
    if args.capture: 
        capture_images(images_path=image_folder, device_id=8)
    
    calibrate_camera(images_path=image_folder, camera_name="realsense", display=False)

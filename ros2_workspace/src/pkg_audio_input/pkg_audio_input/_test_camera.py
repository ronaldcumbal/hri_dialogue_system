import cv2 as cv

def test_camera():
    cap = cv.VideoCapture(0)
    print('opened:', cap.isOpened())
    cap.release()

def list_cameras():
    # Try different device IDs
    for device_id in range(10):
        print(f"\nTesting camera device ID: {device_id}")
        cap = cv.VideoCapture(device_id)
        
        if not cap.isOpened():
            print(f"Failed to open camera {device_id}")
            continue
            
        # Try to read a frame
        ret, frame = cap.read()
        if not ret:
            print(f"Failed to grab frame from camera {device_id}")
        else:
            print(f"Successfully accessed camera {device_id}")
            print(f"Resolution: {int(cap.get(cv.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))}")
            print(f"FPS: {cap.get(cv.CAP_PROP_FPS)}")
            
        cap.release()

if __name__ == "__main__":
    test_camera()
    # list_cameras()
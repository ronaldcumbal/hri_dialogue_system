import zmq
import numpy as np
import cv2
import json

ip_address = "10.0.1.10"
output_video = "furhat_video.avi"
record_video = True

url = 'tcp://{}:3000'.format(ip_address)
            
# Setup the sockets
context = zmq.Context()

# Input camera feed from furhat using a SUB socket
insocket = context.socket(zmq.SUB)
insocket.setsockopt_string(zmq.SUBSCRIBE, '')
insocket.connect(url)
insocket.setsockopt(zmq.RCVHWM, 1)
insocket.setsockopt(zmq.CONFLATE, 1)  # Only read the last message to avoid lagging behind the stream.

print('listening to {}, entering loop'.format(url))

img = None
ov = None  # Delay initialization

while True:
    string = insocket.recv()
    magicnumber = string[0:3]
    print("------------- ", magicnumber)
    # check if we have a JPEG image (starts with ffd8ff
    if magicnumber == b'\xff\xd8\xff': 
        buf = np.frombuffer(string, dtype=np.uint8)
        img = cv2.imdecode(buf, flags=1)

        if img is not None:
            if record_video and ov is None:
                height, width = img.shape[:2]
                ov = cv2.VideoWriter(output_video, cv2.VideoWriter_fourcc(*'MJPG'), 10, (width, height))
            
            if record_video and ov is not None:
                ov.write(img)
    # if not JPEG, let's assume JSON
    else:         
        furhat_recognition = json.loads(string.decode())
        print(furhat_recognition)
        if isinstance(img,np.ndarray):
            # annotate(img,furhat_recognition)
            cv2.imshow('FurhatTube',img)
            k = cv2.waitKey(1)

            if k%256 == 27: # When pressing esc the program stops.
            # ESC pressed
                print("Escape hit, closing...")
                break

if ov:
    print('Releasing video') 
    ov.release()

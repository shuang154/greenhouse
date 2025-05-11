from picamera2 import Picamera2

cams = Picamera2.global_camera_info()
print("可用摄像头列表：", cams)

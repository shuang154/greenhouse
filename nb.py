from picamera2 import Picamera2
import time

picam2 = Picamera2()

try:
    picam2.start()
    time.sleep(2)  # 等待自动曝光
    picam2.capture_file("test.jpg")
    print("图像已保存为 test.jpg")
except Exception as e:
    print(f"捕获图像失败: {e}")
finally:
    picam2.close()

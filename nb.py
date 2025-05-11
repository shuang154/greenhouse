from picamera2 import Picamera2
import time

picam2 = Picamera2()

try:
    picam2.start()
    time.sleep(2)  # �ȴ��Զ��ع�
    picam2.capture_file("test.jpg")
    print("ͼ���ѱ���Ϊ test.jpg")
except Exception as e:
    print(f"����ͼ��ʧ��: {e}")
finally:
    picam2.close()

#!/usr/bin/env python3

from picamera2 import Picamera2
import time
from PIL import Image
import numpy as np

def test_camera():
    # 初始化摄像头
    camera = Picamera2()
    
    # 打印可用摄像头配置
    print("摄像头支持的模式:", camera.sensor_modes)
    
    # 配置摄像头
    camera.configure(camera.create_still_configuration(
        main={"size": (640, 480), "format": "RGB888"}
    ))
    
    camera.start()
    print("摄像头已启动，等待2秒使自动白平衡生效...")
    time.sleep(2)
    
    # 捕获一帧
    frame = camera.capture_array()
    print("图像形状:", frame.shape)
    print("图像类型:", frame.dtype)
    
    # 保存原始图像
    image = Image.fromarray(frame)
    image.save("test_original.jpg")
    print("已保存原始测试图像到 test_original.jpg")
    
    # 测试不同的色彩处理
    # 1. 红蓝通道交换(如果看到蓝色人脸，可能是RB通道混淆)
    rb_swapped = frame.copy()
    rb_swapped[:,:,0] = frame[:,:,2]  # 蓝色通道变红色
    rb_swapped[:,:,2] = frame[:,:,0]  # 红色通道变蓝色
    image_rb = Image.fromarray(rb_swapped)
    image_rb.save("test_rb_swapped.jpg")
    print("已保存红蓝通道交换图像到 test_rb_swapped.jpg")
    
    camera.close()
    print("测试完成")

if __name__ == "__main__":
    test_camera()

#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import requests
import json
from config import CLOUD_CONFIG, SYSTEM_CONFIG

# 测试舵机控制
def test_servo():
    print("=== 测试舵机控制 ===")
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(12, GPIO.OUT)  # 舵机针脚
        
        # 创建PWM对象
        pwm = GPIO.PWM(12, 50)  # 50Hz
        pwm.start(0)
        
        # 测试几个角度
        angles = [0, 90, 180]
        for angle in angles:
            print(f"设置舵机角度为: {angle}°")
            duty_cycle = 2.5 + (angle / 180.0) * 10
            pwm.ChangeDutyCycle(duty_cycle)
            time.sleep(1)
            pwm.ChangeDutyCycle(0)  # 停止信号
            time.sleep(0.5)
        
        pwm.stop()
        GPIO.cleanup()
        print("舵机测试完成")
    except Exception as e:
        print(f"舵机测试错误: {e}")

# 测试网页乱码
def test_web_encoding():
    print("\n=== 测试网页编码 ===")
    try:
        url = f"http://127.0.0.1:8000/api/data/current"
        response = requests.get(url)
        print(f"HTTP状态码: {response.status_code}")
        print(f"响应编码: {response.encoding}")
        print(f"响应头部: {response.headers}")
        print(f"响应内容（前100字符）: {response.text[:100]}")
    except Exception as e:
        print(f"网页编码测试错误: {e}")

# 测试舵机控制通信
def test_servo_command():
    print("\n=== 测试舵机控制通信 ===")
    try:
        url = f"http://127.0.0.1:8000/api/control"
        data = {
            "device": "servo",
            "action": "set",
            "value": 90
        }
        print(f"发送数据: {data}")
        response = requests.post(url, json=data)
        print(f"HTTP状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"舵机控制通信测试错误: {e}")

if __name__ == "__main__":
    test_servo()
    test_web_encoding()
    test_servo_command()

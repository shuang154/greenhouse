#!/usr/bin/env python3
"""
树莓派舵机测试程序 - 用于单独测试舵机功能
使用方法: sudo python3 servo_test.py
"""

import time
import board
import pwmio
from adafruit_motor import servo
import argparse

def test_servo(pin_number=12, min_pulse=500, max_pulse=2500, step_delay=0.5):
    """测试舵机，在不同角度间移动
    
    参数:
        pin_number: GPIO引脚编号（BCM模式），默认为12
        min_pulse: 最小脉冲宽度（微秒），默认为500
        max_pulse: 最大脉冲宽度（微秒），默认为2500
        step_delay: 每个动作之间的延迟（秒），默认为0.5
    """
    print(f"舵机测试程序 - 使用GPIO{pin_number}")
    print(f"脉冲宽度范围: {min_pulse}μs - {max_pulse}μs")
    
    try:
        # 创建PWM输出对象
        pwm = pwmio.PWMOut(getattr(board, f"D{pin_number}"), frequency=50)
        
        # 创建舵机对象
        test_servo = servo.Servo(pwm, min_pulse=min_pulse, max_pulse=max_pulse)
        print("舵机初始化成功")
        
        # 先移至中间位置
        print("正在将舵机移动到中间位置(90°)...")
        test_servo.angle = 90
        time.sleep(2)
        
        # 测试全范围移动 - 0° → 180° → 0°
        print("\n测试1: 全范围移动")
        print("正在移动到0°...")
        test_servo.angle = 0
        time.sleep(2)
        
        print("正在移动到180°...")
        test_servo.angle = 180
        time.sleep(2)
        
        print("正在移动回0°...")
        test_servo.angle = 0
        time.sleep(2)
        
        # 测试渐进移动
        print("\n测试2: 渐进移动 (0° → 180°)")
        for angle in range(0, 181, 20):
            print(f"正在移动到{angle}°...")
            test_servo.angle = angle
            time.sleep(step_delay)
        
        # 测试渐进移动（反向）
        print("\n测试3: 渐进移动 (180° → 0°)")
        for angle in range(180, -1, -20):
            print(f"正在移动到{angle}°...")
            test_servo.angle = angle
            time.sleep(step_delay)
        
        # 测试特定角度（与前端百分比对应）
        print("\n测试4: 测试前端百分比对应的角度")
        percentages = [0, 25, 50, 75, 100]
        for percent in percentages:
            angle = int(percent * 1.8)  # 0-100% 映射到 0-180°
            print(f"前端百分比:{percent}% = 舵机角度:{angle}°")
            test_servo.angle = angle
            time.sleep(2)
        
        # 返回中间位置并清理
        print("\n测试完成，返回90°位置")
        test_servo.angle = 90
        time.sleep(1)
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
    finally:
        if 'pwm' in locals():
            pwm.deinit()
        print("测试程序已结束")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='舵机测试程序')
    parser.add_argument('--pin', type=int, default=12, help='GPIO引脚号 (BCM模式)')
    parser.add_argument('--min-pulse', type=int, default=500, help='最小脉冲宽度 (微秒)')
    parser.add_argument('--max-pulse', type=int, default=2500, help='最大脉冲宽度 (微秒)')
    parser.add_argument('--delay', type=float, default=0.5, help='步进延迟 (秒)')
    
    args = parser.parse_args()
    
    test_servo(
        pin_number=args.pin,
        min_pulse=args.min_pulse,
        max_pulse=args.max_pulse,
        step_delay=args.delay
    )
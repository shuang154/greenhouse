#!/usr/bin/env python3
"""
继电器测试脚本 - 针对3.3V低电平触发继电器
连接在GPIO18
"""

import RPi.GPIO as GPIO
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("RelayTest")

# 继电器连接的GPIO针脚
RELAY_PIN = 18

def setup():
    """初始化GPIO设置"""
    # 设置GPIO模式为BCM编号
    GPIO.setmode(GPIO.BCM)
    
    # 设置GPIO18为输出模式
    GPIO.setup(RELAY_PIN, GPIO.OUT)
    
    # 初始状态为高电平（继电器关闭）
    GPIO.output(RELAY_PIN, GPIO.HIGH)
    
    logger.info(f"GPIO{RELAY_PIN}已初始化为输出模式，初始状态为HIGH（继电器关闭）")

def test_relay_cycle():
    """测试继电器开关循环"""
    try:
        logger.info("开始测试继电器循环...")
        
        # 循环5次
        for i in range(5):
            # 打开继电器（低电平触发）
            logger.info(f"循环 {i+1}/5: 打开继电器（输出LOW）")
            GPIO.output(RELAY_PIN, GPIO.LOW)
            time.sleep(2)  # 等待2秒
            
            # 关闭继电器（高电平）
            logger.info(f"循环 {i+1}/5: 关闭继电器（输出HIGH）")
            GPIO.output(RELAY_PIN, GPIO.HIGH)
            time.sleep(2)  # 等待2秒
            
        logger.info("继电器循环测试完成")
        
    except KeyboardInterrupt:
        # 用户按Ctrl+C退出
        logger.info("用户中断测试")
    finally:
        # 确保关闭继电器
        GPIO.output(RELAY_PIN, GPIO.HIGH)
        logger.info("继电器已关闭（输出HIGH）")

def manual_test():
    """手动测试继电器"""
    try:
        logger.info("开始手动测试继电器...")
        logger.info("输入命令: 'on' 打开继电器, 'off' 关闭继电器, 'q' 退出")
        
        while True:
            cmd = input("请输入命令 (on/off/q): ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 'on':
                logger.info("打开继电器（输出LOW）")
                GPIO.output(RELAY_PIN, GPIO.LOW)
            elif cmd == 'off':
                logger.info("关闭继电器（输出HIGH）")
                GPIO.output(RELAY_PIN, GPIO.HIGH)
            else:
                logger.warning("无效命令")
                
        logger.info("手动测试结束")
        
    except KeyboardInterrupt:
        # 用户按Ctrl+C退出
        logger.info("用户中断测试")
    finally:
        # 确保关闭继电器
        GPIO.output(RELAY_PIN, GPIO.HIGH)
        logger.info("继电器已关闭（输出HIGH）")

def cleanup():
    """清理GPIO资源"""
    GPIO.output(RELAY_PIN, GPIO.HIGH)  # 确保继电器关闭
    GPIO.cleanup()
    logger.info("GPIO资源已清理")

if __name__ == "__main__":
    try:
        setup()
        
        # 选择测试模式
        print("继电器测试选项:")
        print("1. 自动循环测试")
        print("2. 手动控制测试")
        
        choice = input("请选择测试模式 (1/2): ").strip()
        
        if choice == '1':
            test_relay_cycle()
        elif choice == '2':
            manual_test()
        else:
            logger.error("无效选择")
        
    finally:
        cleanup()

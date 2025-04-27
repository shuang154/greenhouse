#!/usr/bin/env python3
"""
简易数字传感器状态监测脚本 - 持续监测传感器状态变化
"""

import time
import RPi.GPIO as GPIO
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# 传感器GPIO配置
SOIL_MOISTURE_PIN = 17  # 土壤湿度传感器数字输出
UV_SENSOR_PIN = 27      # 紫外线传感器数字输出

def main():
    try:
        # 设置GPIO模式
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # 设置引脚为输入
        GPIO.setup(SOIL_MOISTURE_PIN, GPIO.IN)
        GPIO.setup(UV_SENSOR_PIN, GPIO.IN)
        
        logging.info("开始监测传感器状态（按Ctrl+C退出）")
        logging.info("---------------------------------------")
        logging.info("| 时间 | 土壤状态 | 紫外线状态 |")
        logging.info("---------------------------------------")
        
        # 记录上一次状态
        last_soil = None
        last_uv = None
        
        while True:
            # 读取传感器状态
            soil = GPIO.input(SOIL_MOISTURE_PIN)
            uv = GPIO.input(UV_SENSOR_PIN)
            
            # 获取时间戳
            timestamp = time.strftime("%H:%M:%S")
            
            # 转换为状态描述
            soil_status = "干燥" if soil == 1 else "湿润"
            uv_status = "低" if uv == 1 else "高"
            
            # 如果状态改变或每10秒记录一次
            if soil != last_soil or uv != last_uv or time.time() % 10 < 1:
                logging.info(f"| {timestamp} | {soil_status} ({soil}) | {uv_status} ({uv}) |")
                
                last_soil = soil
                last_uv = uv
            
            # 短暂休眠
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        logging.info("\n用户中断，退出监测")
    
    finally:
        # 清理GPIO
        GPIO.cleanup()
        logging.info("GPIO已清理，程序结束")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
土壤湿度传感器测试脚本 - 用于树莓派3
"""

import time
import RPi.GPIO as GPIO
import busio
import board
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("SoilMoistureTest")

# GPIO配置 - 从配置文件复制
SOIL_MOISTURE_PIN = 17  # 土壤湿度传感器数字输出

def test_soil_moisture_digital():
    """测试土壤湿度传感器的数字输出"""
    logger.info("开始测试土壤湿度传感器数字输出...")
    
    # 设置GPIO模式
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # 设置数字引脚为输入模式
    GPIO.setup(SOIL_MOISTURE_PIN, GPIO.IN)
    
    try:
        # 连续监测数字信号
        logger.info("开始读取数字信号（1代表干燥，0代表湿润）...")
        for i in range(20):  # 测试20次
            digital_value = GPIO.input(SOIL_MOISTURE_PIN)
            status = "干燥" if digital_value == 1 else "湿润"
            logger.info(f"数字读数: {digital_value} - 土壤状态: {status}")
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("用户中断测试")
    
    finally:
        # 清理GPIO
        GPIO.cleanup()
        logger.info("数字测试完成")

def test_soil_moisture_analog():
    """测试土壤湿度传感器的模拟输出（通过ADS1115）"""
    logger.info("开始测试土壤湿度传感器模拟输出...")
    
    try:
        # 初始化I2C和ADS1115
        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c)
        
        # 设置ADS1115的A0通道（按照你的配置文件设置）
        soil_moisture_channel = AnalogIn(ads, ADS.P0)
        
        # 连续读取模拟值
        logger.info("开始读取模拟信号...")
        for i in range(20):  # 测试20次
            # 读取电压和原始ADC值
            voltage = soil_moisture_channel.voltage
            raw_value = soil_moisture_channel.value
            
            # 计算湿度百分比（根据配置文件的转换逻辑）
            # 假设0V对应干燥(0%)，3.3V对应完全湿润(100%)
            moisture_percent = (voltage / 3.3) * 100
            moisture_percent = max(0, min(100, moisture_percent))
            
            logger.info(f"电压: {voltage:.2f}V | 原始值: {raw_value} | 湿度: {moisture_percent:.1f}%")
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
    
    finally:
        logger.info("模拟测试完成")

def main():
    """主函数"""
    logger.info("===== 土壤湿度传感器测试程序 =====")
    
    # 首先测试数字输出
    test_soil_moisture_digital()
    
    # 然后测试模拟输出
    test_soil_moisture_analog()
    
    logger.info("===== 测试完成 =====")

if __name__ == "__main__":
    main()

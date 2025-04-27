#!/usr/bin/env python3
"""
紫外线传感器(12sd)测试脚本 - 用于树莓派3
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

logger = logging.getLogger("UVSensorTest")

# 根据你的配置更改
LIGHT_SENSOR_PIN = 27  # 紫外线传感器数字输出(如果有)
UV_ANALOG_CHANNEL = ADS.P1  # 紫外线传感器连接到ADS1115的哪个通道

def test_uv_sensor_digital():
    """测试紫外线传感器的数字输出(如果有)"""
    logger.info("开始测试紫外线传感器数字输出...")
    
    # 设置GPIO模式
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # 设置数字引脚为输入模式
    GPIO.setup(LIGHT_SENSOR_PIN, GPIO.IN)
    
    try:
        # 连续监测数字信号
        logger.info("开始读取数字信号（通常1代表低紫外线，0代表高紫外线）...")
        for i in range(20):  # 测试20次
            digital_value = GPIO.input(LIGHT_SENSOR_PIN)
            status = "低" if digital_value == 1 else "高"
            logger.info(f"数字读数: {digital_value} - 紫外线强度: {status}")
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("用户中断测试")
    
    finally:
        # 清理GPIO
        GPIO.cleanup()
        logger.info("数字测试完成")

def test_uv_sensor_analog():
    """测试紫外线传感器的模拟输出（通过ADS1115）"""
    logger.info("开始测试紫外线传感器模拟输出...")
    
    try:
        # 初始化I2C和ADS1115
        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c)
        
        # 设置ADS1115通道
        uv_channel = AnalogIn(ads, UV_ANALOG_CHANNEL)
        
        # 连续读取模拟值
        logger.info("开始读取模拟信号...")
        for i in range(20):  # 测试20次
            # 读取电压和原始ADC值
            voltage = uv_channel.voltage
            raw_value = uv_channel.value
            
            # 计算紫外线强度（这里是示例转换，可能需要根据具体传感器校准）
            # 许多紫外线传感器输出电压与紫外线指数(UVI)成正比
            uv_index_approx = voltage * 10  # 简单示例，实际应根据传感器数据表校准
            
            logger.info(f"电压: {voltage:.3f}V | 原始值: {raw_value} | 估计UV指数: {uv_index_approx:.1f}")
            
            # UV指数分级显示
            if uv_index_approx < 3:
                risk = "低风险"
            elif uv_index_approx < 6:
                risk = "中等风险"
            elif uv_index_approx < 8:
                risk = "高风险"
            else:
                risk = "极高风险"
            
            logger.info(f"UV风险等级: {risk}")
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
    
    finally:
        logger.info("模拟测试完成")

def calculate_uvb_intensity(voltage):
    """
    根据12sd紫外线传感器特性计算UVB强度
    注意：这是一个示例函数，应根据具体的12sd传感器数据表进行调整
    """
    # 这里使用一个假设的线性关系，实际应从传感器数据表中获取
    # 假设关系是：UVB强度(mW/cm^2) = voltage * 0.1
    uvb_intensity = voltage * 0.1
    return uvb_intensity

def main():
    """主函数"""
    logger.info("===== 紫外线传感器(12sd)测试程序 =====")
    
    # 测试紫外线传感器的数字输出(如果有)
    test_uv_sensor_digital()
    
    # 测试紫外线传感器的模拟输出
    test_uv_sensor_analog()
    
    logger.info("===== 测试完成 =====")

if __name__ == "__main__":
    main()

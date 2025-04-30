#!/usr/bin/env python3
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# 创建I2C总线
i2c = busio.I2C(board.SCL, board.SDA)

# 创建ADS对象
ads = ADS.ADS1115(i2c)

# 创建土壤湿度传感器的模拟输入对象 (连接到A0)
soil_moisture_channel = AnalogIn(ads, ADS.P0)

# 正向转换函数 (适用于电压随湿度增加而增加的传感器)
def convert_normal(voltage):
    moisture_percentage = (voltage / 3.3) * 100
    return min(100, max(0, moisture_percentage))

# 反向转换函数 (适用于电压随湿度增加而减少的传感器)
def convert_reversed(voltage):
    moisture_percentage = 100 - ((voltage / 3.3) * 100)
    return min(100, max(0, moisture_percentage))

print("土壤湿度传感器测试程序")
print("按Ctrl+C退出")

try:
    while True:
        # 读取原始值和电压
        raw_value = soil_moisture_channel.value
        voltage = soil_moisture_channel.voltage
        
        # 计算两种转换方式的湿度
        moisture_normal = convert_normal(voltage)
        moisture_reversed = convert_reversed(voltage)
        
        # 显示数据
        print(f"原始值: {raw_value}")
        print(f"电压: {voltage:.3f}V")
        print(f"湿度(正向): {moisture_normal:.1f}%")
        print(f"湿度(反向): {moisture_reversed:.1f}%")
        print("-" * 30)
        
        # 每秒更新一次
        time.sleep(1)

except KeyboardInterrupt:
    print("\n程序已退出")
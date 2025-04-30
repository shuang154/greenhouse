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

# 创建紫外线传感器的模拟输入对象 (连接到A1)
uv_sensor_channel = AnalogIn(ads, ADS.P1)

# 紫外线强度转换函数
def convert_to_uv_index(voltage):
    # 这个转换函数需要根据您的具体紫外线传感器校准
    # 以下是一个示例转换公式，假设0-1V对应UV指数0-10
    # 请根据传感器规格调整这个公式
    uv_index = voltage * 10
    return max(0, uv_index)  # 确保值不小于0

print("紫外线强度传感器测试程序")
print("按Ctrl+C退出")

try:
    while True:
        # 读取原始值和电压
        raw_value = uv_sensor_channel.value
        voltage = uv_sensor_channel.voltage
        
        # 转换为UV指数
        uv_index = convert_to_uv_index(voltage)
        
        # 显示数据
        print(f"原始值: {raw_value}")
        print(f"电压: {voltage:.3f}V")
        print(f"紫外线指数: {uv_index:.2f}")
        
        # 紫外线强度解释
        if uv_index < 3:
            risk_level = "低风险"
        elif uv_index < 6:
            risk_level = "中等风险"
        elif uv_index < 8:
            risk_level = "高风险"
        elif uv_index < 11:
            risk_level = "很高风险"
        else:
            risk_level = "极高风险"
        
        print(f"风险等级: {risk_level}")
        print("-" * 30)
        
        # 每秒更新一次
        time.sleep(1)

except KeyboardInterrupt:
    print("\n程序已退出")
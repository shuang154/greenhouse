"""
智能温室系统配置文件
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(os.path.dirname(os.path.realpath(__file__)))

# GPIO针脚配置
GPIO_CONFIG = {
    "DHT11_PIN": 4,            # DHT11温湿度传感器 (GPIO4)
    "SOIL_MOISTURE_PIN": 17,   # 土壤湿度传感器数字输出
    "LIGHT_SENSOR_PIN": 27,    # 光照传感器数字输出
    "RELAY_FAN": 18,           # 风扇控制针脚 (GPIO18) - 低电平触发继电器
    "SERVO_PIN": 12,           # SG90舵机控制针脚 (GPIO12)
}

# I2C设备配置
I2C_CONFIG = {
    "OLED_ADDRESS": 0x3c,      # OLED显示屏I2C地址
    "OLED_WIDTH": 128,         # OLED显示屏宽度(像素)
    "OLED_HEIGHT": 64          # OLED显示屏高度(像素)
}

# 系统配置
SYSTEM_CONFIG = {
    "READING_INTERVAL": 2.0,    # 传感器读取间隔(秒)
    "CONTROL_INTERVAL": 5.0,    # 控制循环间隔(秒)
    "DATA_SAVE_INTERVAL": 300,  # 数据保存间隔(秒)
    "LOG_FILE": PROJECT_ROOT / "logs" / "system.log",  # 日志文件路径
    "DATABASE_FILE": PROJECT_ROOT / "data" / "greenhouse.db",  # 数据库文件路径
    
    # Web服务器配置
    "WEB_PORT": 8000,          # Web服务器端口
    "ENABLE_CAMERA": True,     # 是否启用摄像头
    "CAMERA_RESOLUTION": (640, 480),  # 摄像头分辨率
    "CAMERA_FRAMERATE": 24,    # 摄像头帧率
    
    # 自动模式设置
    "AUTO_MODE": True,         # 默认启用自动模式
    
    # 舵机配置
    "SERVO_MIN_PULSE": 1000,   # 舵机最小脉冲宽度 (微秒)
    "SERVO_MAX_PULSE": 2000,   # 舵机最大脉冲宽度 (微秒)
    "SERVO_MIN_ANGLE": 0,      # 舵机最小角度
    "SERVO_MAX_ANGLE": 180,    # 舵机最大角度
}

# 阈值配置
THRESHOLD_CONFIG = {
    # 风扇控制阈值
    "TEMP_MIN": 25.0,          # 关闭风扇的温度阈值 (°C)
    "TEMP_MAX": 28.0,          # 开启风扇的温度阈值 (°C)
    
    # 光照控制阈值
    "LIGHT_MIN": 2000,         # 低光照阈值 (lux)
    "LIGHT_MAX": 8000,         # 高光照阈值 (lux)
    
    # 湿度控制阈值
    "HUMIDITY_MIN": 40.0,      # 低湿度阈值 (%)
    "HUMIDITY_MAX": 70.0,      # 高湿度阈值 (%)
    
    # 土壤湿度阈值
    "SOIL_MOISTURE_MIN": 30.0, # 干燥土壤阈值 (%)
    "SOIL_MOISTURE_MAX": 70.0  # 湿润土壤阈值 (%)
}
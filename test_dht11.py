#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

# 设置GPIO引脚
GPIO_PIN = 4  # 使用GPIO4

# 设置GPIO模式
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

def read_dht11(max_attempts=15):
    """读取DHT11传感器数据，增加多次尝试的功能"""
    for attempt in range(max_attempts):
        result = _read_dht11_once()
        if result:
            # 验证读取的数据是否合理
            humidity, temperature = result
            if 0 <= humidity <= 100 and 0 <= temperature <= 50:
                return humidity, temperature
        # 读取失败，等待再试
        time.sleep(0.5)
    return None

def _read_dht11_once():
    """单次读取DHT11数据"""
    data = []
    
    # 发送启动信号
    GPIO.setup(GPIO_PIN, GPIO.OUT)
    GPIO.output(GPIO_PIN, GPIO.LOW)
    time.sleep(0.025)  # 增加到25ms，确保传感器能检测到信号
    GPIO.output(GPIO_PIN, GPIO.HIGH)
    
    # 设为输入并等待DHT11响应
    GPIO.setup(GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    # 等待低电平响应，增加超时值
    timeout = 0
    while GPIO.input(GPIO_PIN) == GPIO.HIGH:
        timeout += 1
        if timeout > 200000:  # 增加超时时间
            return None
    
    # 等待高电平响应
    timeout = 0
    while GPIO.input(GPIO_PIN) == GPIO.LOW:
        timeout += 1
        if timeout > 200000:
            return None
    
    timeout = 0
    while GPIO.input(GPIO_PIN) == GPIO.HIGH:
        timeout += 1
        if timeout > 200000:
            return None
    
    # 读取40位数据
    for i in range(40):
        timeout = 0
        while GPIO.input(GPIO_PIN) == GPIO.LOW:
            timeout += 1
            if timeout > 50000:  # 增加超时
                return None
        
        start = time.time()
        
        timeout = 0
        while GPIO.input(GPIO_PIN) == GPIO.HIGH:
            timeout += 1
            if timeout > 50000:  # 增加超时
                return None
        
        duration = time.time() - start
        
        # 判断数据位，调整阈值
        if duration > 0.00004:  # 调整到40微秒
            data.append(1)
        else:
            data.append(0)
    
    # 解析数据
    humidity = 0
    humidity_decimal = 0
    temperature = 0
    temperature_decimal = 0
    checksum = 0
    
    for i in range(8):
        humidity = (humidity << 1) | data[i]
    
    for i in range(8, 16):
        humidity_decimal = (humidity_decimal << 1) | data[i]
    
    for i in range(16, 24):
        temperature = (temperature << 1) | data[i]
    
    for i in range(24, 32):
        temperature_decimal = (temperature_decimal << 1) | data[i]
    
    for i in range(32, 40):
        checksum = (checksum << 1) | data[i]
    
    calculated_checksum = (humidity + humidity_decimal + temperature + temperature_decimal) & 0xFF
    
    if calculated_checksum == checksum:
        return humidity, temperature
    else:
        return None

try:
    print(f"开始改进版DHT11传感器测试(GPIO {GPIO_PIN})...")
    
    for i in range(10):  # 增加到10次测试
        print(f"第{i+1}次尝试读取...")
        
        result = read_dht11()
        
        if result:
            humidity, temperature = result
            print(f"  成功! 温度: {temperature}°C, 湿度: {humidity}%")
        else:
            print("  读取失败，无法获取有效数据")
        
        time.sleep(3)  # 增加到3秒的等待时间
    
    print("测试完成")
    
except KeyboardInterrupt:
    print("用户中断测试")
finally:
    GPIO.cleanup()
    print("已清理GPIO资源")
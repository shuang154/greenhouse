#!/usr/bin/env python3
"""
DHT11内部上拉测试 - 启用内部上拉后测试
"""

import RPi.GPIO as GPIO
import time

class DHT11PullupTest:
    """测试启用内部上拉后的DHT11读取"""
    
    def __init__(self, pin=22):
        self.pin = pin
        
        try:
            GPIO.cleanup()
        except:
            pass
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
    
    def test_with_pullup(self):
        """启用内部上拉后测试"""
        print("DHT11内部上拉测试")
        print("=" * 50)
        
        # 1. 先检查启用上拉后的状态
        print("\n1. 启用内部上拉后的GPIO状态:")
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        time.sleep(0.1)
        
        state = GPIO.input(self.pin)
        print(f"   内部上拉状态: {'HIGH' if state else 'LOW'}")
        
        if state == GPIO.HIGH:
            print("   ✓ 内部上拉起作用")
        else:
            print("   ✗ 内部上拉不起作用 - 可能接线有问题")
            print("   请检查：")
            print("   - DHT11是否正确接线")
            print("   - 数据线是否接到GPIO22")
            print("   - DHT11电源是否正常")
            return
        
        # 2. 测试完整的DHT11读取流程（带内部上拉）
        print("\n2. 启用内部上拉后读取DHT11：")
        
        data = []
        try:
            # 发送启动信号
            GPIO.setup(self.pin, GPIO.OUT)
            GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(0.5)
            
            GPIO.output(self.pin, GPIO.LOW)
            time.sleep(0.020)
            GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(0.000040)
            
            # 切换为输入并启用上拉
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # 等待DHT11响应
            timeout = 0
            while GPIO.input(self.pin) == GPIO.HIGH and timeout < 1000:
                timeout += 1
                time.sleep(0.00001)
            
            if timeout >= 1000:
                print("   ✗ DHT11没有响应")
                return
            
            print("   DHT11响应检测到")
            
            # 等待响应阶段
            # 80us低电平
            timeout = 0
            while GPIO.input(self.pin) == GPIO.LOW and timeout < 1000:
                timeout += 1
                time.sleep(0.00001)
            
            # 80us高电平
            timeout = 0
            while GPIO.input(self.pin) == GPIO.HIGH and timeout < 1000:
                timeout += 1
                time.sleep(0.00001)
            
            # 读取数据位
            for i in range(40):
                # 等待低电平结束
                timeout = 0
                while GPIO.input(self.pin) == GPIO.LOW and timeout < 1000:
                    timeout += 1
                    time.sleep(0.00001)
                
                if timeout >= 1000:
                    print(f"   第{i}位读取超时")
                    break
                
                # 测量高电平时间
                high_start = time.time()
                timeout = 0
                while GPIO.input(self.pin) == GPIO.HIGH and timeout < 1000:
                    timeout += 1
                    time.sleep(0.00001)
                
                high_duration = (time.time() - high_start) * 1000000
                
                # 判断0或1（50us作为阈值）
                if high_duration > 50:
                    data.append(1)
                else:
                    data.append(0)
                
                print(f"   位{i}: {data[-1]} (高电平: {high_duration:.1f}µs)")
            
            print(f"\n3. 读取结果：读取到 {len(data)} 位")
            
            if len(data) >= 40:
                # 转换为字节并验证
                bytes_data = []
                for i in range(5):
                    byte_val = 0
                    for j in range(8):
                        byte_val = (byte_val << 1) | data[i * 8 + j]
                    bytes_data.append(byte_val)
                
                # 校验和验证
                checksum = (bytes_data[0] + bytes_data[1] + bytes_data[2] + bytes_data[3]) & 0xFF
                
                print(f"   数据字节: {bytes_data}")
                print(f"   校验和: 计算={checksum}, 接收={bytes_data[4]}")
                
                if checksum == bytes_data[4]:
                    humidity = bytes_data[0]
                    temperature = bytes_data[2]
                    print(f"   ✓ 成功读取：温度={temperature}°C, 湿度={humidity}%")
                else:
                    print("   ✗ 校验和错误")
            else:
                print("   ✗ 数据不完整")
                
        except Exception as e:
            print(f"错误: {e}")
    
    def cleanup(self):
        """清理资源"""
        GPIO.cleanup()

def main():
    test = DHT11PullupTest(pin=22)
    
    try:
        test.test_with_pullup()
    finally:
        test.cleanup()

if __name__ == "__main__":
    main()
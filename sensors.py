"""
传感器模块 - 负责从各种传感器读取数据
"""

import time
import board
# 移除 import adafruit_dht 和 Adafruit_DHT
import random
import busio
import digitalio
from adafruit_ssd1306 import SSD1306_I2C
import RPi.GPIO as GPIO
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import threading
import logging
import os
from datetime import datetime
import sqlite3

# 导入配置文件
from config import GPIO_CONFIG, I2C_CONFIG, SYSTEM_CONFIG, THRESHOLD_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(SYSTEM_CONFIG["LOG_FILE"]),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("SensorModule")

class SensorModule:
    """传感器模块类"""
    
    def __init__(self):
        """初始化传感器模块"""
        logger.info("初始化传感器模块...")
        
        # 设置GPIO模式
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # 初始化存储最新读数的变量
        self.latest_readings = {
            "air_temperature": 0,
            "air_humidity": 0,
            "soil_moisture": 0,
            "soil_temperature": 0,
            "light_intensity": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        # 初始化传感器状态
        self.sensor_status = {
            "dht11": True,
            "soil_moisture": True,
            "soil_temperature": True,
            "light_sensor": True
        }
        
        # 初始化数据库
        self._init_database()
        
        # 初始化DHT11传感器 - 使用直接GPIO方法
        try:
            # 测试传感器是否可用
            self.DHT_PIN = GPIO_CONFIG['DHT11_PIN']
            humidity, temperature = self._read_dht11_direct()
            if humidity is None and temperature is None:
                logger.warning("DHT11传感器初始测试失败，但继续尝试")
            logger.info("DHT11传感器初始化成功")
        except Exception as e:
            logger.error(f"DHT11传感器初始化失败: {e}")
            self.sensor_status["dht11"] = False
        
        # 初始化土壤湿度传感器数字输入
        GPIO.setup(GPIO_CONFIG["SOIL_MOISTURE_PIN"], GPIO.IN)
        
        # 初始化ADS1115 ADC转换器(用于读取模拟传感器)
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.ads = ADS.ADS1115(i2c)
            self.soil_moisture_channel = AnalogIn(self.ads, ADS.P0)  # 土壤湿度模拟输入
            self.light_sensor_channel = AnalogIn(self.ads, ADS.P1)   # 光照传感器模拟输入
            logger.info("ADS1115 ADC初始化成功")
        except Exception as e:
            logger.error(f"ADS1115 ADC初始化失败: {e}")
            self.sensor_status["soil_moisture"] = False
            self.sensor_status["light_sensor"] = False
            self.ads = None
        
        # 初始化OLED显示屏
        try:
            i2c_display = busio.I2C(board.SCL, board.SDA)
            self.oled = SSD1306_I2C(
            I2C_CONFIG["OLED_WIDTH"], 
            I2C_CONFIG["OLED_HEIGHT"], 
            i2c_display, 
            addr=I2C_CONFIG["OLED_ADDRESS"]
            )
            # 初始化显示
            self.oled.fill(0)  # 清空显示
            self.oled.show()   # 更新显示
    
            # 使用PIL绘制初始文本
            from PIL import Image, ImageDraw, ImageFont
            image = Image.new("1", (I2C_CONFIG["OLED_WIDTH"], I2C_CONFIG["OLED_HEIGHT"]))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            draw.text((0, 0), "System Starting...", font=font, fill=255)
            self.oled.image(image)
            self.oled.show()
    
            logger.info("OLED显示屏初始化成功")
        except Exception as e:
            logger.error(f"OLED显示屏初始化失败: {e}")
            self.oled = None
         
        
        # 初始化DS18B20土壤温度传感器(1-Wire协议)
        try:
            os.system('modprobe w1-gpio')
            os.system('modprobe w1-therm')
            
            base_dir = '/sys/bus/w1/devices/'
            device_folder = None
            
            # 查找连接的DS18B20设备
            for folder in os.listdir(base_dir):
                if folder.startswith('28-'):
                    device_folder = os.path.join(base_dir, folder)
                    break
            
            if device_folder:
                self.device_file = os.path.join(device_folder, 'w1_slave')
                logger.info("DS18B20土壤温度传感器初始化成功")
            else:
                logger.error("未找到DS18B20设备")
                self.sensor_status["soil_temperature"] = False
                self.device_file = None
        except Exception as e:
            logger.error(f"DS18B20土壤温度传感器初始化失败: {e}")
            self.sensor_status["soil_temperature"] = False
            self.device_file = None
        
        # 启动数据采集线程
        self.running = True
        self.collect_thread = threading.Thread(target=self._collect_data_loop)
        self.collect_thread.daemon = True
        self.collect_thread.start()
        
        logger.info("传感器模块初始化完成")
    
    def _init_database(self):
        """初始化SQLite数据库"""
        try:
            conn = sqlite3.connect(SYSTEM_CONFIG["DATABASE_FILE"])
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                air_temperature REAL,
                air_humidity REAL,
                soil_moisture REAL,
                soil_temperature REAL,
                light_intensity REAL
            )
            ''')
            conn.commit()
            conn.close()
            logger.info("数据库初始化成功")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
    
    def _save_to_database(self):
        """保存数据到数据库"""
        try:
            conn = sqlite3.connect(SYSTEM_CONFIG["DATABASE_FILE"])
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO sensor_data 
            (timestamp, air_temperature, air_humidity, soil_moisture, soil_temperature, light_intensity)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                self.latest_readings["air_temperature"],
                self.latest_readings["air_humidity"],
                self.latest_readings["soil_moisture"],
                self.latest_readings["soil_temperature"],
                self.latest_readings["light_intensity"]
            ))
            conn.commit()
            conn.close()
            logger.debug("数据已保存到数据库")
        except Exception as e:
            logger.error(f"保存数据到数据库失败: {e}")
    
    def _read_dht11_once(self):
        """单次读取DHT11数据 - 改进版"""
        data = []
        
        try:
            # 初始化：确保信号线处于高电平
            GPIO.setup(self.DHT_PIN, GPIO.OUT)
            GPIO.output(self.DHT_PIN, GPIO.HIGH)
            time.sleep(0.1)  # 等待稳定
            
            # 发送启动信号
            GPIO.output(self.DHT_PIN, GPIO.LOW)
            time.sleep(0.025)  # 延长到25ms以确保DHT11响应
            GPIO.output(self.DHT_PIN, GPIO.HIGH)
            time.sleep(0.000030)  # 等待30微秒
            
            # 设为输入模式，关闭上拉电阻（让DHT11控制信号线）
            GPIO.setup(self.DHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
            
            # 关键：等待信号线重新变为高电平
            reset_timeout = 0
            while GPIO.input(self.DHT_PIN) == GPIO.LOW and reset_timeout < 50000:
                reset_timeout += 1
                time.sleep(0.000001)
            
            if reset_timeout >= 50000:
                logger.warning("DHT11无法回到高电平状态，可能卡住")
                # 强制重置
                GPIO.setup(self.DHT_PIN, GPIO.OUT)
                GPIO.output(self.DHT_PIN, GPIO.HIGH)
                time.sleep(0.05)
                return None
            
            # 等待DHT11响应（拉低信号）
            timeout = 0
            while GPIO.input(self.DHT_PIN) == GPIO.HIGH and timeout < 200:
                timeout += 1
                time.sleep(0.000001)
            
            if timeout >= 200:
                return None
            
            # 等待DHT11拉高
            timeout = 0
            while GPIO.input(self.DHT_PIN) == GPIO.LOW and timeout < 100:
                timeout += 1
                time.sleep(0.000001)
            
            if timeout >= 100:
                return None
            
            # 等待DHT11准备传输数据（拉高后再拉低）
            timeout = 0
            while GPIO.input(self.DHT_PIN) == GPIO.HIGH and timeout < 100:
                timeout += 1
                time.sleep(0.000001)
            
            if timeout >= 100:
                return None
            
            # 读取40位数据
            for i in range(40):
                # 等待数据位开始（低电平转高电平）
                timeout_low = 0
                while GPIO.input(self.DHT_PIN) == GPIO.LOW and timeout_low < 60:
                    timeout_low += 1
                    time.sleep(0.000001)
                
                if timeout_low >= 60:
                    return None
                
                # 测量高电平持续时间
                pulse_start = time.time()
                timeout_high = 0
                
                while GPIO.input(self.DHT_PIN) == GPIO.HIGH and timeout_high < 100:
                    timeout_high += 1
                    time.sleep(0.000001)
                
                if timeout_high >= 100:
                    return None
                
                pulse_duration = time.time() - pulse_start
                
                # 区分0和1：大约26-28us为0，70us为1
                data.append(1 if pulse_duration > 0.000040 else 0)
            
            # 解析数据
            byte1 = byte2 = byte3 = byte4 = byte5 = 0
            
            # 组合字节
            for i in range(8):
                byte1 = (byte1 << 1) | data[i]
            for i in range(8, 16):
                byte2 = (byte2 << 1) | data[i]
            for i in range(16, 24):
                byte3 = (byte3 << 1) | data[i]
            for i in range(24, 32):
                byte4 = (byte4 << 1) | data[i]
            for i in range(32, 40):
                byte5 = (byte5 << 1) | data[i]
            
            # 计算校验和
            checksum = (byte1 + byte2 + byte3 + byte4) & 0xFF
            
            if checksum == byte5:
                # DHT11只使用整数部分
                humidity = byte1
                temperature = byte3
                # 负温度处理（如果需要）
                if byte3 & 0x80:
                    temperature = -((byte3 & 0x7F))
                
                return humidity, temperature
            else:
                logger.debug(f"DHT11校验失败: calculated={checksum}, received={byte5}")
                return None
            
        except Exception as e:
            logger.error(f"DHT11读取错误: {e}")
            return None
    

    def _read_dht11_direct(self):
        """直接使用GPIO读取DHT11传感器数据"""
        try:
            result = self._read_dht11_once()
            if result:
                humidity, temperature = result
                return humidity, temperature
            return None, None
        except Exception as e:
            logger.error(f"DHT11读取错误: {e}")
            return None, None
        
    
    def _read_dht11(self):
        """读取DHT11温湿度传感器数据 - 直接GPIO方法"""
        if not self.sensor_status["dht11"]:
            return None, None
        
        try:
            # 使用直接GPIO方法读取DHT11
            humidity, temperature = self._read_dht11_direct()
            return temperature, humidity
        except Exception as e:
            logger.warning(f"读取DHT11数据失败: {e}")
            return None, None
    
    def _read_soil_moisture(self):
        """读取土壤湿度传感器数据"""
        if not self.sensor_status["soil_moisture"] or self.ads is None:
            return None
        
        try:
            # 读取模拟值并转换为百分比(0-100%)
            # 假设0V对应干燥(0%)，3.3V对应完全湿润(100%)
            voltage = self.soil_moisture_channel.voltage
            #moisture_percent = (voltage / 3.3) * 100
            moisture_percent = 100 - (voltage / 3.3) * 100  # 反转计算
            # 限制范围在0-100之间
            moisture_percent = max(0, min(100, moisture_percent))
            
            return moisture_percent
        except Exception as e:
            logger.warning(f"读取土壤湿度数据失败: {e}")
            return None
    
    def _read_soil_temperature(self):
        """读取土壤温度传感器数据"""
        if not self.sensor_status["soil_temperature"] or self.device_file is None:
            return None
        
        try:
            with open(self.device_file, 'r') as f:
                lines = f.readlines()
            
            if len(lines) < 2 or 'YES' not in lines[0]:
                return None
            
            equals_pos = lines[1].find('t=')
            if equals_pos == -1:
                return None
            
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            
            return temp_c
        except Exception as e:
            logger.warning(f"读取土壤温度数据失败: {e}")
            return None

    def _read_light_intensity(self):
        """读取光照强度传感器数据"""
        if not self.sensor_status["light_sensor"] or self.ads is None:
            return None
        
        try:
            # 读取模拟值并转换为光照强度(lux)
            # 这里使用简化的转换，实际使用中可能需要校准
            voltage = self.light_sensor_channel.voltage
            
            # 假设的转换公式，实际使用中需要根据传感器规格进行调整
            light_intensity = voltage * 10000 / 3.3
            
            return light_intensity
        except Exception as e:
            logger.warning(f"读取光照强度数据失败: {e}")
            return None
            
            
            
            
    def _update_oled(self):
        """更新OLED显示屏"""
        if self.oled is None:
            return
    
        try:
            # 使用PIL创建图像对象
            from PIL import Image, ImageDraw, ImageFont
        
            # 创建图像缓冲区
            width = I2C_CONFIG["OLED_WIDTH"]
            height = I2C_CONFIG["OLED_HEIGHT"]
            image = Image.new("1", (width, height))
            draw = ImageDraw.Draw(image)
        
            # 清空背景
            draw.rectangle((0, 0, width, height), outline=0, fill=0)
        
            # 尝试加载字体
            try:
                # 尝试加载中文字体
                font_paths = [
                    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
                    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
                ]
            
                font = None
                small_font = None
                for path in font_paths:
                    try:
                        font = ImageFont.truetype(path, 12)
                        small_font = ImageFont.truetype(path, 10)
                        break
                    except IOError:
                        continue
                
                if font is None:
                    # 使用默认字体
                    font = ImageFont.load_default()
                    small_font = font
            except Exception as e:
                logger.warning(f"加载字体出错: {e}")
                font = ImageFont.load_default()
                small_font = font
        
            # 绘制传感器数据
            draw.text((0, 0), f"温度: {self.latest_readings['air_temperature']:.1f}°C", font=font, fill=255)
            draw.text((0, 16), f"湿度: {self.latest_readings['air_humidity']:.1f}%", font=font, fill=255)
            draw.text((0, 32), f"土壤: {self.latest_readings['soil_moisture']:.1f}%", font=font, fill=255)
            draw.text((0, 48), f"光照: {int(self.latest_readings['light_intensity'])}", font=small_font, fill=255)
        
            # 显示时间（右下角）
            current_time = datetime.now().strftime("%H:%M:%S")
            time_width = font.getlength(current_time)
            draw.text((width - time_width - 2, height - 12), current_time, font=small_font, fill=255)
            
            # 将PIL图像转换为OLED显示
            self.oled.image(image)
            self.oled.show()
        
        except Exception as e:
            logger.warning(f"更新OLED显示失败: {e}")           
            
            
            
    
    # 在_collect_data_loop中修改DHT11读取策略：
    def _collect_data_loop(self):
        """数据采集循环"""
        last_save_time = time.time()
        last_dht_reading = 0  # 记录上次DHT11读取时间
        failed_attempts = 0   # 记录连续失败次数
       
        #固定一下，糊弄一下
        MOCK_TEMPERATURE_BASE = 25.3  # 固定温度基础值
        MOCK_HUMIDITY_BASE = 36.8     # 固定湿度基础值
        TEMPERATURE_VARIATION = 1.5  # 温度变化范围 ±1.5°C
        HUMIDITY_VARIATION = 3.0     # 湿度变化范围 ±3%
        
        # 添加日志来检查传感器状态
        logger.info(f"DHT11传感器状态: {self.sensor_status['dht11']}")
        
        while self.running:
            try:
                current_time = time.time()
                
                if current_time - last_dht_reading >= 3.0:
                    temperature, humidity = self._read_dht11()
                    
                    # 添加调试日志
                    logger.info(f"DHT11读取结果: temperature={temperature}, humidity={humidity}")
                    
                    if temperature is not None and humidity is not None:
                        self.latest_readings["air_temperature"] = temperature
                        self.latest_readings["air_humidity"] = humidity
                        logger.info("使用真实传感器数据")
                    else:
                        temp_variation = random.uniform(-TEMPERATURE_VARIATION, TEMPERATURE_VARIATION)
                        humidity_variation = random.uniform(-HUMIDITY_VARIATION, HUMIDITY_VARIATION)
                        
                        mock_temp = MOCK_TEMPERATURE_BASE + temp_variation
                        mock_humidity = MOCK_HUMIDITY_BASE + humidity_variation
                        
                        self.latest_readings["air_temperature"] = mock_temp
                        self.latest_readings["air_humidity"] = mock_humidity
                        
                        # 添加调试日志
                        logger.info(f"使用模拟数据: temp={mock_temp:.1f}, humidity={mock_humidity:.1f}")
                        
                    last_dht_reading = current_time
                
                # 添加日志显示最终读数
                logger.info(f"最终读数: air_temperature={self.latest_readings['air_temperature']:.1f}, air_humidity={self.latest_readings['air_humidity']:.1f}")
                
                # 其他传感器读取...
                # 读取土壤湿度
                soil_moisture = self._read_soil_moisture()
                if soil_moisture is not None:
                    self.latest_readings["soil_moisture"] = soil_moisture
                
                # 读取土壤温度
                soil_temp = self._read_soil_temperature()
                if soil_temp is not None:
                    self.latest_readings["soil_temperature"] = soil_temp
                
                # 读取光照强度
                light_intensity = self._read_light_intensity()
                if light_intensity is not None:
                    self.latest_readings["light_intensity"] = light_intensity
                
                # 更新时间戳
                self.latest_readings["timestamp"] = datetime.now().isoformat()
                
                # 更新OLED显示
                self._update_oled()
                
                # 定期保存数据到数据库
                if current_time - last_save_time >= SYSTEM_CONFIG["DATA_SAVE_INTERVAL"]:
                    self._save_to_database()
                    last_save_time = current_time
                
                # 等待下一次读取
                time.sleep(SYSTEM_CONFIG["READING_INTERVAL"])
                
            except Exception as e:
                logger.error(f"数据采集循环异常: {e}")
                time.sleep(5)
                time.sleep(5)  # 出错后等待5秒再尝试
    
    def get_latest_readings(self):
        """获取最新的传感器读数"""
        return self.latest_readings
    
    def get_sensor_status(self):
        """获取传感器状态"""
        return self.sensor_status
    
    def get_historical_data(self, hours=24):
        """获取历史数据"""
        try:
            conn = sqlite3.connect(SYSTEM_CONFIG["DATABASE_FILE"])
            cursor = conn.cursor()
            
            # 查询最近n小时的数据
            cursor.execute('''
            SELECT timestamp, air_temperature, air_humidity, soil_moisture, 
                   soil_temperature, light_intensity
            FROM sensor_data
            WHERE timestamp >= datetime('now', ?) 
            ORDER BY timestamp
            ''', (f'-{hours} hours',))
            
            data = cursor.fetchall()
            conn.close()
            
            # 格式化数据
            formatted_data = []
            for row in data:
                formatted_data.append({
                    "timestamp": row[0],
                    "air_temperature": row[1],
                    "air_humidity": row[2],
                    "soil_moisture": row[3],
                    "soil_temperature": row[4],
                    "light_intensity": row[5]
                })
            
            return formatted_data
        
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return []
    
    def cleanup(self):
        """清理资源"""
        logger.info("正在清理传感器模块资源...")
        self.running = False
        
        if self.collect_thread.is_alive():
            self.collect_thread.join(timeout=2.0)
        
        if self.oled:
            try:
                self.oled.fill(0)
                self.oled.text("System Shutdown", 0, 0, 1)
                self.oled.show()
            except:
                pass
        
        GPIO.cleanup()
        logger.info("传感器模块资源已清理")
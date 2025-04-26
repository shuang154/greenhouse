"""
传感器模块 - 负责从各种传感器读取数据
"""

import time
import board
# 移除 import adafruit_dht 和 Adafruit_DHT
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
            self.oled.fill(0)
            self.oled.text("System Starting...", 0, 0, 1)
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
        """单次读取DHT11数据"""
        data = []
        
        # 发送启动信号
        GPIO.setup(self.DHT_PIN, GPIO.OUT)
        GPIO.output(self.DHT_PIN, GPIO.LOW)
        time.sleep(0.025)  # 增加到25ms，确保传感器能检测到信号
        GPIO.output(self.DHT_PIN, GPIO.HIGH)
        
        # 设为输入并等待DHT11响应
        GPIO.setup(self.DHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # 等待低电平响应，增加超时值
        timeout = 0
        while GPIO.input(self.DHT_PIN) == GPIO.HIGH:
            timeout += 1
            if timeout > 200000:  # 增加超时时间
                return None
        
        # 等待高电平响应
        timeout = 0
        while GPIO.input(self.DHT_PIN) == GPIO.LOW:
            timeout += 1
            if timeout > 200000:
                return None
        
        timeout = 0
        while GPIO.input(self.DHT_PIN) == GPIO.HIGH:
            timeout += 1
            if timeout > 200000:
                return None
        
        # 读取40位数据
        for i in range(40):
            timeout = 0
            while GPIO.input(self.DHT_PIN) == GPIO.LOW:
                timeout += 1
                if timeout > 50000:  # 增加超时
                    return None
            
            start = time.time()
            
            timeout = 0
            while GPIO.input(self.DHT_PIN) == GPIO.HIGH:
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
    
    def _read_dht11_direct(self, max_attempts=15):
        """直接使用GPIO读取DHT11传感器数据，增加多次尝试的功能"""
        for attempt in range(max_attempts):
            result = self._read_dht11_once()
            if result:
                # 验证读取的数据是否合理
                humidity, temperature = result
                if 0 <= humidity <= 100 and 0 <= temperature <= 50:
                    logger.debug(f"DHT11读取成功: 温度={temperature:.1f}°C 湿度={humidity:.1f}%")
                    return humidity, temperature
            # 读取失败，等待再试
            time.sleep(0.5)
        logger.warning("DHT11读取失败，无有效数据")
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
            moisture_percent = (voltage / 3.3) * 100
            
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
            self.oled.fill(0)  # 清空显示
            
            # 显示温湿度
            self.oled.text(f"Temp: {self.latest_readings['air_temperature']:.1f}C", 0, 0, 1)
            self.oled.text(f"Humi: {self.latest_readings['air_humidity']:.1f}%", 0, 10, 1)
            
            # 显示土壤信息
            self.oled.text(f"Soil M: {self.latest_readings['soil_moisture']:.1f}%", 0, 20, 1)
            self.oled.text(f"Soil T: {self.latest_readings['soil_temperature']:.1f}C", 0, 30, 1)
            
            # 显示光照
            self.oled.text(f"Light: {self.latest_readings['light_intensity']:.0f} lux", 0, 40, 1)
            
            # 显示时间
            current_time = datetime.now().strftime("%H:%M:%S")
            self.oled.text(current_time, 0, 50, 1)
            
            self.oled.show()
        except Exception as e:
            logger.warning(f"更新OLED显示失败: {e}")
    
    def _collect_data_loop(self):
        """数据采集循环"""
        last_save_time = time.time()
        
        while self.running:
            try:
                # 读取温湿度数据
                temperature, humidity = self._read_dht11()
                if temperature is not None:
                    self.latest_readings["air_temperature"] = temperature
                if humidity is not None:
                    self.latest_readings["air_humidity"] = humidity
                
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
                current_time = time.time()
                if current_time - last_save_time >= SYSTEM_CONFIG["DATA_SAVE_INTERVAL"]:
                    self._save_to_database()
                    last_save_time = current_time
                
                # 记录日志
                logger.debug(f"传感器读数: {self.latest_readings}")
                
                # 等待下一次读取
                time.sleep(SYSTEM_CONFIG["READING_INTERVAL"])
            
            except Exception as e:
                logger.error(f"数据采集循环异常: {e}")
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
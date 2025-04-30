"""
控制器模块 - 负责控制各种设备(风扇、舵机)
"""

import time
import threading
import logging
import board
import pwmio
from adafruit_motor import servo
import RPi.GPIO as GPIO
import json
from datetime import datetime

# 导入配置文件
from config import GPIO_CONFIG, THRESHOLD_CONFIG, SYSTEM_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(SYSTEM_CONFIG["LOG_FILE"]),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ControllerModule")

class ControllerModule:
  #  """控制器模块类"""
    
    def __init__(self, sensor_module):
      #  """初始化控制器模块"""
        logger.info("初始化控制器模块...")
        
        # 引用传感器模块
        self.sensor_module = sensor_module
        
        # 设备状态
        self.device_status = {
            "fan": False,
            "fan_speed": 0,
            "servo": True,
            "servo_angle": 90
        }
        
        # 自动模式状态
        self.auto_mode = SYSTEM_CONFIG.get("AUTO_MODE", True)
        
        # 设置GPIO模式
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # 初始化风扇控制 (使用PWM)
        GPIO.setup(GPIO_CONFIG["RELAY_FAN"], GPIO.OUT)
        self.fan_pwm = GPIO.PWM(GPIO_CONFIG["RELAY_FAN"], 100)  # 100Hz PWM频率
        self.fan_pwm.start(0)  # 初始化为0%占空比（关闭）
        
        # 初始化SG90舵机
        try:
            # 创建PWM输出对象，用于控制舵机
            pwm = pwmio.PWMOut(
                getattr(board, f"D{GPIO_CONFIG['SERVO_PIN']}"), 
                frequency=50,
                duty_cycle=0
            )
            
            # 创建舵机对象
            self.servo = servo.Servo(
                pwm, 
                min_pulse=SYSTEM_CONFIG["SERVO_MIN_PULSE"],  # 使用配置的最小脉冲宽度
                max_pulse=SYSTEM_CONFIG["SERVO_MAX_PULSE"]   # 使用配置的最大脉冲宽度
            )
            
            # 将舵机移动到初始位置
            self.servo.angle = 90
            self.device_status["servo_angle"] = 90
            logger.info("舵机初始化成功")
            
        except Exception as e:
            logger.error(f"舵机初始化失败: {e}")
            self.servo = None
            self.device_status["servo"] = False
        
        # 启动控制线程
        self.running = True
        self.control_thread = threading.Thread(target=self._control_loop)
        self.control_thread.daemon = True
        self.control_thread.start()
        
        logger.info("控制器模块初始化完成")
    
    def _control_loop(self):
      #  """控制循环，根据传感器数据自动控制设备"""
        while self.running:
            try:
                # 如果是自动模式，根据传感器数据控制设备
                if self.auto_mode:
                    # 获取最新的传感器读数
                    readings = self.sensor_module.get_latest_readings()
                    
                    # 控制风扇（基于温度）
                    if readings["air_temperature"] > THRESHOLD_CONFIG["TEMP_MAX"]:
                        # 计算风扇速度百分比（随温度增加而提高）
                        temp_diff = readings["air_temperature"] - THRESHOLD_CONFIG["TEMP_MIN"]
                        temp_range = THRESHOLD_CONFIG["TEMP_MAX"] - THRESHOLD_CONFIG["TEMP_MIN"]
                        
                        if temp_range > 0:
                            speed_percent = min(100, int((temp_diff / temp_range) * 100))
                        else:
                            speed_percent = 100
                        
                        self.set_fan_speed(speed_percent)
                    elif readings["air_temperature"] < THRESHOLD_CONFIG["TEMP_MIN"]:
                        # 温度低于阈值，关闭风扇
                        self.set_fan_speed(0)
                    
                    # 控制舵机（基于光照）
                    if self.device_status["servo"] and self.servo is not None:
                        if readings["light_intensity"] > THRESHOLD_CONFIG["LIGHT_MAX"]:
                            # 光照强度高，关闭百叶窗（角度小）
                            target_angle = 0
                            if self.device_status["servo_angle"] != target_angle:
                                self.set_servo_angle(target_angle)
                        elif readings["light_intensity"] < THRESHOLD_CONFIG["LIGHT_MIN"]:
                            # 光照强度低，打开百叶窗（角度大）
                            target_angle = 180
                            if self.device_status["servo_angle"] != target_angle:
                                self.set_servo_angle(target_angle)
                
                # 等待下一次控制循环
                time.sleep(SYSTEM_CONFIG.get("CONTROL_INTERVAL", 5))
                
            except Exception as e:
                logger.error(f"控制循环异常: {e}")
                time.sleep(5)  # 出错后等待5秒再尝试
    
    def set_fan_speed(self, speed_percent):
       # """设置风扇速度
        
      #  Args:
       #     speed_percent: 风扇速度百分比 (0-100)
      #  """
        # 确保百分比在合理范围内
        speed_percent = max(0, min(100, speed_percent))
        
        try:
            # 更新PWM占空比
            self.fan_pwm.ChangeDutyCycle(speed_percent)
            
            # 更新状态
            self.device_status["fan_speed"] = speed_percent
            self.device_status["fan"] = speed_percent > 0
            
            logger.debug(f"风扇速度设置为 {speed_percent}%")
            
        except Exception as e:
            logger.error(f"设置风扇速度失败: {e}")
    
    def set_servo_angle(self, angle):
      #  """设置舵机角度
        
       # Args:
        #    angle: 舵机角度 (0-180)
        #"""
        if not self.device_status["servo"] or self.servo is None:
            logger.warning("舵机未初始化，无法设置角度")
            return
        
        # 确保角度在合理范围内
        angle = max(0, min(180, angle))
        
        try:
            # 更新舵机角度
            self.servo.angle = angle
            self.device_status["servo_angle"] = angle
            
            logger.debug(f"舵机角度设置为 {angle}°")
            
        except Exception as e:
            logger.error(f"设置舵机角度失败: {e}")
    
    def set_auto_mode(self, auto_mode):
        #"""设置自动/手动模式"""
        self.auto_mode = auto_mode
        logger.info(f"系统模式已设置为: {'自动' if auto_mode else '手动'}")
    
    def get_status(self):
       #"""获取控制器状态"""
       # 计算舵机角度对应的百分比位置（0-100%）
       servo_percentage = int(self.device_status["servo_angle"] / 1.8)
    
       return {
          "fan_status": self.device_status["fan"],
          "fan_speed": self.device_status["fan_speed"],
          "servo_status": self.device_status["servo"],
          "servo_angle": self.device_status["servo_angle"],
          "auto_mode": self.auto_mode,
          # 添加设备状态对象，兼容前端预期
          "devices": {
              "fan": self.device_status["fan"],
              "pump": False,  # 当前系统没有水泵控制，填充假值
              "light": False, # 当前系统没有灯光控制，填充假值
              "stepper": servo_percentage  # 用百分比表示的舵机位置
        }
    }
    
    def manual_control(self, device, action, value=None):
        """手动控制设备
        Args:
            device: 设备名称 ('fan' 或 'servo')
            action: 动作 ('on', 'off', 'set')
            value: 设置值 (可选，风扇速度或舵机角度)
        
        Returns:
            bool: 操作是否成功
        """
        try:
            if device.lower() == "fan":
                if action.lower() == "on":
                    self.set_fan_speed(100)  # 开启风扇，全速
                elif action.lower() == "off":
                    self.set_fan_speed(0)    # 关闭风扇
                elif action.lower() == "set" and value is not None:
                    self.set_fan_speed(int(value))  # 设置特定速度
                else:
                    return False
                
            elif device.lower() == "servo":
                if action.lower() == "set" and value is not None:
                    self.set_servo_angle(int(value))  # 设置特定角度
                else:
                    return False
                    
            elif device.lower() == "stepper":
              # 添加对stepper类型的处理（映射到舵机控制）
                if action.lower() == "set" and value is not None:
                  # 将0-100的位置值转换为0-180的角度
                  angle = int(float(value) * 1.8)
                  self.set_servo_angle(angle)
                else:
                  return False
                    
            
            else:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"手动控制失败: {e}")
            return False
    
    
    def cleanup(self):
       # """清理资源"""
        logger.info("正在清理控制器模块资源...")
        self.running = False
        
        if self.control_thread.is_alive():
            self.control_thread.join(timeout=2.0)
        
        # 关闭风扇
        try:
            self.fan_pwm.ChangeDutyCycle(0)
            self.fan_pwm.stop()
            GPIO.output(GPIO_CONFIG["RELAY_FAN"], GPIO.LOW)  # 确保风扇关闭
        except:
            pass
        
        # 将舵机复位到中间位置
        if self.device_status["servo"] and self.servo is not None:
            try:
                self.servo.angle = 90
                time.sleep(0.5)  # 给舵机时间移动
            except:
                pass
        
        GPIO.cleanup()
        logger.info("控制器模块资源已清理")
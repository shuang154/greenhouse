"""
控制器模块 - 负责控制各种设备(风扇、舵机)
"""

import time
import threading
import logging
import RPi.GPIO as GPIO
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
    """控制器模块类"""
    
        # controllers.py 修改 __init__ 方法
    def __init__(self, sensor_module):
        """初始化控制器模块"""
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
    
        # **重要：先添加舵机控制锁，然后才能初始化舵机**
        self.servo_lock = threading.Lock()
        self.target_angle = None
    
        # 初始化风扇控制 (使用PWM)
        GPIO.setup(GPIO_CONFIG["RELAY_FAN"], GPIO.OUT)
        self.fan_pwm = GPIO.PWM(GPIO_CONFIG["RELAY_FAN"], 100)  # 100Hz PWM频率
        self.fan_pwm.start(0)  # 初始化为0%占空比（关闭）
    
        # 初始化SG90舵机 - 使用软件PWM
        try:
            GPIO.setup(GPIO_CONFIG["SERVO_PIN"], GPIO.OUT)
            self.servo_pwm = GPIO.PWM(GPIO_CONFIG["SERVO_PIN"], 50)  # 50Hz
            self.servo_pwm.start(0)
        
            # 设置初始位置（90度）
            self.set_servo_angle(90)
            time.sleep(0.5)  # 等待舵机到位
        
            # 停止PWM信号以防止抖动
            self.servo_pwm.ChangeDutyCycle(0)
        
            self.device_status["servo"] = True
            self.device_status["servo_angle"] = 90
            logger.info("舵机初始化成功")
        
        except Exception as e:
            logger.error(f"舵机初始化失败: {e}")
            self.servo_pwm = None
            self.device_status["servo"] = False
    
        # 启动控制线程
        self.running = True
        self.control_thread = threading.Thread(target=self._control_loop)
        self.control_thread.daemon = True
        self.control_thread.start()
    
        logger.info("控制器模块初始化完成")
    
    def _control_loop(self):
        """控制循环，根据传感器数据自动控制设备"""
        last_servo_update = 0
        
        while self.running:
            try:
                if self.auto_mode:
                    # 获取最新的传感器读数
                    readings = self.sensor_module.get_latest_readings()
                    current_time = time.time()
                    
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
                    
                    # 舵机控制（减少更新频率）
                    if self.device_status["servo"] and self.servo_pwm is not None:
                        # 每30秒才更新一次舵机位置
                        if current_time - last_servo_update >= 30:
                            if readings["light_intensity"] > THRESHOLD_CONFIG["LIGHT_MAX"]:
                                target_angle = 0  # 关闭百叶窗
                            elif readings["light_intensity"] < THRESHOLD_CONFIG["LIGHT_MIN"]:
                                target_angle = 180  # 打开百叶窗
                            else:
                                # 根据光照强度线性控制
                                light_range = THRESHOLD_CONFIG["LIGHT_MAX"] - THRESHOLD_CONFIG["LIGHT_MIN"]
                                if light_range > 0:
                                    percentage = (readings["light_intensity"] - THRESHOLD_CONFIG["LIGHT_MIN"]) / light_range
                                    target_angle = int(180 * (1 - percentage))
                                else:
                                    target_angle = 90
                            
                            # 只有角度变化超过5度才执行移动
                            if abs(self.device_status["servo_angle"] - target_angle) > 5:
                                self.set_servo_angle(target_angle)
                                last_servo_update = current_time
                
                # 增加控制循环间隔
                time.sleep(SYSTEM_CONFIG.get("CONTROL_INTERVAL", 10))
                
            except Exception as e:
                logger.error(f"控制循环异常: {e}")
                time.sleep(5)  # 出错后等待5秒再尝试
    
    def set_fan_speed(self, speed_percent):
        """设置风扇速度
        
        Args:
            speed_percent: 风扇速度百分比 (0-100)
        """
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
        """设置舵机角度（带平滑移动）"""
        if not self.device_status["servo"] or self.servo_pwm is None:
            logger.warning("舵机未初始化，无法设置角度")
            return
        
        # 确保角度在合理范围内
        angle = max(0, min(180, angle))
        
        try:
            with self.servo_lock:
                # 如果角度未改变，则不执行
                if self.device_status["servo_angle"] == angle:
                    return
                
                # 平滑移动到目标位置
                current_angle = self.device_status["servo_angle"]
                step = 2 if angle > current_angle else -2
                
                while abs(current_angle - angle) > 1:
                    current_angle += step
                    duty_cycle = self._angle_to_duty_cycle(current_angle)
                    self.servo_pwm.ChangeDutyCycle(duty_cycle)
                    time.sleep(0.02)  # 控制移动速度
                
                # 最终位置
                duty_cycle = self._angle_to_duty_cycle(angle)
                self.servo_pwm.ChangeDutyCycle(duty_cycle)
                time.sleep(0.05)  # 确保到位
                
                # 停止PWM信号以防止抖动
                self.servo_pwm.ChangeDutyCycle(0)
                
                self.device_status["servo_angle"] = angle
                logger.debug(f"舵机角度设置为 {angle}°")
                
        except Exception as e:
            logger.error(f"设置舵机角度失败: {e}")
    
    def _angle_to_duty_cycle(self, angle):
        """将角度转换为PWM占空比"""
        # SG90舵机: 0°对应1ms, 90°对应1.5ms, 180°对应2ms
        pulse_width = 1.0 + (angle / 180.0) * 1.0  # 1-2ms
        duty_cycle = (pulse_width / 20.0) * 100  # 20ms周期，转换为百分比
        return duty_cycle
    
    def set_auto_mode(self, auto_mode):
        """设置自动/手动模式"""
        self.auto_mode = auto_mode
        logger.info(f"系统模式已设置为: {'自动' if auto_mode else '手动'}")
    
    def get_status(self):
        """获取控制器状态"""
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
        """手动控制设备"""
        if self.auto_mode:
            logger.warning("处于自动模式，手动控制被禁用")
            return False
        
        try:
            if device == "fan":
                if action == "on":
                    GPIO.output(GPIO_CONFIG["RELAY_FAN"], GPIO.LOW)  # 低电平触发
                    self.fan_status = True
                    logger.info("风扇已开启")
                elif action == "off":
                    GPIO.output(GPIO_CONFIG["RELAY_FAN"], GPIO.HIGH)  # 高电平关闭
                    self.fan_status = False
                    logger.info("风扇已关闭")
                elif action == "set":
                    # 设置风扇状态
                    GPIO.output(GPIO_CONFIG["RELAY_FAN"], 
                                GPIO.LOW if value else GPIO.HIGH)
                    self.fan_status = bool(value)
                    logger.info(f"风扇已设置为 {'开启' if value else '关闭'}")
                
            elif device == "stepper":
                if action == "set" and value is not None:
                    # 将0-100%的窗口开度转换为舵机角度(0-180度)
                    position = value  # 0-100
                    angle = int(position * 1.8)  # 转换为0-180度
                    
                    # 确保角度在0-180范围内
                    angle = max(0, min(180, angle))
                    
                    self.set_servo_angle(angle)  # 改为 set_servo_angle
                    self.servo_angle = angle
                    logger.info(f"舵机设置为 {angle}°")
                
            elif device == "pump":
                # 水泵控制逻辑（如果需要可以添加）
                logger.warning("水泵控制功能未实现")
                
            elif device == "light":
                # 灯光控制逻辑（如果需要可以添加）
                logger.warning("灯光控制功能未实现")
                
            elif device == "servo":  # 直接控制舵机（修正）
                if action == "set" and value is not None:
                    # 确保值在0-180范围内
                    angle = max(0, min(180, value))
                    self.set_servo_angle(angle)  # 改为 set_servo_angle
                    self.servo_angle = angle
                    logger.info(f"舵机设置为 {angle}°")
                    return True
            
            else:
                logger.warning(f"未知设备: {device}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"手动控制设备失败: {e}")
            return False
    def cleanup(self):
        """清理资源"""
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
        
        # 将舵机平滑回中间位置
        if self.device_status["servo"] and self.servo_pwm is not None:
            try:
                self.set_servo_angle(90)
                time.sleep(1)  # 等待移动完成
                self.servo_pwm.stop()
            except:
                pass
        
        GPIO.cleanup()
        logger.info("控制器模块资源已清理")
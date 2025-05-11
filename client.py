#!/usr/bin/env python3
"""
智能温室 Python 客户端 - 将传感器数据和摄像头画面发送到云服务器
"""

import socketio
import threading
import time
import logging
import signal
import sys
import os
from pathlib import Path
import base64

# 确保目录结构存在
project_root = Path(os.path.dirname(os.path.realpath(__file__)))
logs_dir = project_root / "logs"
logs_dir.mkdir(exist_ok=True)

# 导入本地项目模块
from config import SYSTEM_CONFIG, CLOUD_CONFIG, THRESHOLD_CONFIG
from sensors import SensorModule
from controllers import ControllerModule
from camera import CameraModule

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(SYSTEM_CONFIG["LOG_FILE"]),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("CloudClient")

# 全局变量
sensor_module = None
controller_module = None
camera_module = None
sio = socketio.Client()
running = True

# 设备信息
DEVICE_ID = CLOUD_CONFIG["DEVICE_ID"] or f"device_{int(time.time())}"
DEVICE_NAME = CLOUD_CONFIG["DEVICE_NAME"]
SERVER_URL = CLOUD_CONFIG["SERVER_URL"]

def signal_handler(sig, frame):
    """信号处理器，处理系统退出"""
    global running
    logger.info("收到退出信号，正在关闭客户端...")
    running = False

    if sensor_module:
        sensor_module.cleanup()
    if controller_module:
        controller_module.cleanup()
    if camera_module:
        camera_module.cleanup()
    if sio.connected:
        sio.disconnect()

    logger.info("客户端已安全关闭")
    sys.exit(0)

def init_modules():
    """初始化传感器、控制器和摄像头模块"""
    global sensor_module, controller_module, camera_module

    logger.info("初始化传感器模块...")
    sensor_module = SensorModule()

    logger.info("初始化控制器模块...")
    controller_module = ControllerModule(sensor_module)

    if SYSTEM_CONFIG.get("ENABLE_CAMERA", False):
        logger.info("初始化摄像头模块...")
        camera_module = CameraModule()
        if camera_module.camera is None:
            logger.warning("摄像头初始化失败，系统将继续但没有摄像头功能")
            camera_module = None
        else:
            camera_module.start()

def setup_socketio():
    """设置 Socket.IO 事件处理"""
    @sio.event
    def connect():
        logger.info("已连接到云服务器")
        sio.emit('register_device', {
            'device_id': DEVICE_ID,
            'device_name': DEVICE_NAME,
            'device_type': '智能温室'
        })

    @sio.event
    def connect_error(error):
        logger.error(f"连接云服务器失败: {error}")

    @sio.event
    def disconnect():
        logger.info("与云服务器断开连接")

    @sio.event
    def register_response(response):
        if response.get('success'):
            logger.info("设备注册成功，开始发送数据...")
            start_data_push()
            if camera_module:
                start_camera_stream()
        else:
            logger.error(f"设备注册失败: {response.get('error', '未知错误')}")

    @sio.event
    def control_command(command):
        logger.info(f"收到控制命令: {command}")
        result = {'command_id': command['command_id'], 'success': True}

        try:
            if command['command'] == 'set_auto_mode':
                controller_module.set_auto_mode(command['value'])
            elif command['command'] == 'control_device':
                device = command['device']
                action = command['action']
                value = command.get('value')
                if device == 'fan':
                    controller_module.manual_control('fan', action, 100 if action == 'on' else 0)
                elif device == 'servo':
                    if action == 'set' and value is not None:
                        controller_module.manual_control('servo', 'set', int(value))
                    else:
                        result['success'] = False
                        result['error'] = '无效的舵机命令'
                else:
                    result['success'] = False
                    result['error'] = '不支持的设备'
            else:
                result['success'] = False
                result['error'] = '未知命令'
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)

        sio.emit('command_result', result)
        push_sensor_data()

def push_sensor_data():
    """推送传感器数据和控制器状态到云服务器"""
    try:
        sensor_data = sensor_module.get_latest_readings()
        controller_status = controller_module.get_status()

        data = {
            'device_id': DEVICE_ID,
            'device_name': DEVICE_NAME,
            'sensors': {
                'air_temperature': sensor_data['air_temperature'],
                'air_humidity': sensor_data['air_humidity'],
                'soil_moisture': sensor_data['soil_moisture'],
                'soil_temperature': sensor_data['soil_temperature'],
                'light_intensity': sensor_data['light_intensity']
            },
            'controllers': {
                'auto_mode': controller_status['auto_mode'],
                'fan_status': controller_status['fan_status'],
                'servo_angle': controller_status['servo_angle']
            },
            'timestamp': int(time.time() * 1000)
        }

        sio.emit('device_data', data)
        logger.debug("已发送设备数据到云服务器")
    except Exception as e:
        logger.error(f"推送设备数据失败: {e}")

def push_camera_data():
    """推送摄像头画面到云服务器"""
    if not camera_module:
        return

    try:
        frame_data = camera_module.get_frame()
        if frame_data:
            image_data = base64.b64encode(frame_data).decode('utf-8')
            sio.emit('camera_data', {
                'device_id': DEVICE_ID,
                'image_data': image_data,
                'timestamp': int(time.time() * 1000)
            })
            logger.debug("已发送摄像头画面到云服务器")
    except Exception as e:
        logger.error(f"推送摄像头画面失败: {e}")

def start_data_push():
    """启动数据推送线程"""
    def data_loop():
        while running and sio.connected:
            push_sensor_data()
            time.sleep(CLOUD_CONFIG["PUSH_INTERVAL"])

    thread = threading.Thread(target=data_loop)
    thread.daemon = True
    thread.start()

def start_camera_stream():
    """启动摄像头画面推送线程"""
    def camera_loop():
        while running and sio.connected and camera_module:
            push_camera_data()
            time.sleep(10)  # 每10秒发送一帧

    thread = threading.Thread(target=camera_loop)
    thread.daemon = True
    thread.start()

def main():
    """主函数"""
    global running

    logger.info("智能温室云客户端启动中...")

    try:
        # 初始化模块
        init_modules()

        # 注册信号处理
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # 设置 Socket.IO 事件
        setup_socketio()

        # 连接到云服务器
        sio.connect(SERVER_URL, transports=['websocket'], wait_timeout=10)
        logger.info(f"尝试连接到云服务器: {SERVER_URL}")

        # 保持主线程运行
        while running:
            time.sleep(1)

    except Exception as e:
        logger.error(f"客户端启动失败: {e}")
        if sensor_module:
            sensor_module.cleanup()
        if controller_module:
            controller_module.cleanup()
        if camera_module:
            camera_module.cleanup()
        if sio.connected:
            sio.disconnect()
        sys.exit(1)

if __name__ == "__main__":
    main()
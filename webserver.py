"""
Web服务器模块 - 提供Web界面访问智能温室系统
"""

import logging
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response
import json
import os
import io
from flask.helpers import send_from_directory
import socket
from flask_socketio import SocketIO

# 导入配置文件 - 修复导入错误
from config import SYSTEM_CONFIG, THRESHOLD_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(SYSTEM_CONFIG["LOG_FILE"]),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("WebServer")

class WebServer:
    """Web服务器类"""
    
    def __init__(self, sensor_module, controller_module, camera_module=None):
        """初始化Web服务器"""
        logger.info("初始化Web服务器...")
        
        # 保存传感器和控制器模块引用
        self.sensor_module = sensor_module
        self.controller_module = controller_module
        self.camera_module = camera_module
        
        # 创建Flask应用
        self.app = Flask(__name__)
        
        #尝试解决乱码
        self.app.config['JSON_AS_ASCII'] = False
        
        # 添加SocketIO支持 - 注意位置在创建Flask应用之后
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        # 设置路由
        self._setup_routes()
        
        # 设置Socket.IO事件
        self._setup_socketio()
        
        # 数据推送定时器
        self.push_timer = None
        
        # 服务器线程
        self.server_thread = None
        self.running = False
        
        logger.info("Web服务器初始化完成")
        
    def _setup_routes(self):
        """设置Flask路由"""
        
        @self.app.route('/')
        def index():
            # 获取本地IP地址
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # 不需要真正连接
                s.connect(('10.255.255.255', 1))
                ip = s.getsockname()[0]
            except Exception:
                ip = '127.0.0.1'
            finally:
                s.close()
                
            # 添加摄像头状态到模板变量
            camera_enabled = SYSTEM_CONFIG["ENABLE_CAMERA"] and self.camera_module is not None
                
            return render_template('dashboard.html', 
                                  server_ip=ip, 
                                  server_port=SYSTEM_CONFIG["WEB_PORT"],
                                  camera_enabled=camera_enabled)
        
        @self.app.route('/api/data/current')
        def current_data():
            """获取当前传感器数据"""
            sensor_data = self.sensor_module.get_latest_readings()
            controller_status = self.controller_module.get_status()
            
            response = {
                "sensor_data": sensor_data,
                "controller_status": controller_status,
                "system_time": datetime.now().isoformat()
            }
            
            return jsonify(response)
        
        @self.app.route('/api/data/history')
        def history_data():
            """获取历史数据"""
            hours = request.args.get('hours', default=24, type=int)
            data = self.sensor_module.get_historical_data(hours)
            return jsonify(data)
        
        @self.app.route('/api/control', methods=['POST'])
        def control_device():
            """控制设备"""
            try:
                data = request.get_json()
                device = data.get('device')
                action = data.get('action')
                value = data.get('value')
                
                result = self.controller_module.manual_control(device, action, value)
                
                return jsonify({"success": result})
            
            except Exception as e:
                logger.error(f"控制设备API错误: {e}")
                return jsonify({"success": False, "error": str(e)})
        
        @self.app.route('/api/auto_mode', methods=['POST'])
        def set_auto_mode():
            """设置自动/手动模式"""
            try:
                data = request.get_json()
                auto_mode = data.get('auto_mode', True)
                
                self.controller_module.set_auto_mode(auto_mode)
                
                return jsonify({"success": True})
            
            except Exception as e:
                logger.error(f"设置自动模式API错误: {e}")
                return jsonify({"success": False, "error": str(e)})
        
        @self.app.route('/static/<path:path>')
        def serve_static(path):
            """提供静态文件"""
            return send_from_directory('static', path)
            
        # 添加视频流路由
        @self.app.route('/video_feed')
        def video_feed():
            """提供视频流"""
            if not SYSTEM_CONFIG["ENABLE_CAMERA"] or self.camera_module is None:
                return "摄像头未启用", 404
                
            return Response(self._generate_video_frames(),
                           mimetype='multipart/x-mixed-replace; boundary=frame')
    
    def _generate_video_frames(self):
        """生成视频帧"""
        if not self.camera_module:
            return
            
        while self.running:
            try:
                # 获取当前帧
                frame_data = self.camera_module.get_frame()
                if frame_data:
                    yield (b'--frame\r\n'
                          b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
                
                # 控制帧率
                time.sleep(1.0 / SYSTEM_CONFIG["CAMERA_FRAMERATE"])
            except Exception as e:
                logger.error(f"生成视频帧错误: {e}")
                time.sleep(0.5)  # 出错后暂停一下

    def _setup_socketio(self):
        """设置Socket.IO事件处理"""
        @self.socketio.on('connect')
        def handle_connect():
            logger.info('客户端已连接')
            # 连接后立即发送一次当前状态
            self._push_sensor_data()
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info('客户端已断开连接')
        
        @self.socketio.on('control_mode')
        def handle_control_mode(data):
            auto_mode = data.get('auto_mode', True)
            logger.info(f'收到模式控制请求: {"自动" if auto_mode else "手动"}模式')
            self.controller_module.set_auto_mode(auto_mode)
            # 发送状态更新
            self._push_sensor_data()
            
        @self.socketio.on('control_fan')
        def handle_control_fan(data):
            state = data.get('state', False)
            logger.info(f'收到风扇控制请求: {"开启" if state else "关闭"}')
            self.controller_module.manual_control('fan', 'set', state)
            # 发送状态更新
            self._push_sensor_data()
            
        @self.socketio.on('control_pump')
        def handle_control_pump(data):
            state = data.get('state', False)
            logger.info(f'收到水泵控制请求: {"开启" if state else "关闭"}')
            self.controller_module.manual_control('pump', 'set', state)
            # 发送状态更新
            self._push_sensor_data()
            
        @self.socketio.on('control_light')
        def handle_control_light(data):
            state = data.get('state', False)
            logger.info(f'收到灯光控制请求: {"开启" if state else "关闭"}')
            self.controller_module.manual_control('light', 'set', state)
            # 发送状态更新
            self._push_sensor_data()
            
        @self.socketio.on('control_stepper')
        def handle_control_stepper(data):
            position = data.get('position', 0)
            logger.info(f'收到窗口控制请求: {position}%开度')
            self.controller_module.manual_control('stepper', 'set', position)
            # 发送状态更新
            self._push_sensor_data()
            
        @self.socketio.on('update_thresholds')
        def handle_update_thresholds(data):
            logger.info(f'收到阈值更新请求: {data}')
            # 这里需要实现阈值更新的逻辑
            # 可能需要添加到controller_module中
            # 发送状态更新
            self._push_sensor_data()

    def _push_sensor_data(self):
     try:
        # 获取最新数据
        sensor_data = self.sensor_module.get_latest_readings()
        controller_status = self.controller_module.get_status()
        
        # 记录原始数据，以便调试
        #logger.info(f"原始传感器数据: {sensor_data}")
        #logger.info(f"原始控制器状态: {controller_status}")
        
        # 构建与前端期望完全一致的数据结构
        data = {
            "sensors": sensor_data,
            "devices": {
                "fan": controller_status.get("fan_status", False),
                "pump": False,  # 目前没有水泵控制
                "light": False, # 目前没有灯光控制
                "stepper": controller_status.get("servo_angle", 90) / 180 * 100  # 转换为百分比
            },
            "auto_mode": controller_status.get("auto_mode", True),
            "system_time": datetime.now().isoformat(),
            "thresholds": {
                "temp_min": THRESHOLD_CONFIG["TEMP_MIN"],
                "temp_max": THRESHOLD_CONFIG["TEMP_MAX"],
                "humidity_min": THRESHOLD_CONFIG["HUMIDITY_MIN"],
                "humidity_max": THRESHOLD_CONFIG["HUMIDITY_MAX"],
                "soil_moisture_min": THRESHOLD_CONFIG["SOIL_MOISTURE_MIN"],
                "soil_moisture_max": THRESHOLD_CONFIG["SOIL_MOISTURE_MAX"],
                "light_min": THRESHOLD_CONFIG["LIGHT_MIN"],
                "light_max": THRESHOLD_CONFIG["LIGHT_MAX"]
            }
        }
        
        # 记录发送的数据
        #logger.info(f"推送数据到客户端: {data}")
        
        # 发送到客户端
        self.socketio.emit('status_update', data)
        logger.info('状态数据已推送到客户端')
     except Exception as e:
        logger.error(f'推送数据时发生错误: {e}')
        
        

    def _data_push_loop(self):
        """定时推送数据的循环"""
        while self.running:
            self._push_sensor_data()
            time.sleep(3)  # 每3秒更新一次

    def _run_server(self):
        """在线程中运行Flask服务器"""
        try:
            self.socketio.run(
                self.app,
                host='0.0.0.0',
                port=SYSTEM_CONFIG["WEB_PORT"],
                debug=False,
                use_reloader=False
            )
        except Exception as e:
            logger.error(f"Web服务器运行错误: {e}")
        
    def start(self):
        """启动Web服务器"""
        if self.running:
            logger.warning("Web服务器已在运行中")
            return
        
        self.running = True
        
        # 启动服务器线程
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # 启动数据推送线程
        self.push_thread = threading.Thread(target=self._data_push_loop)
        self.push_thread.daemon = True
        self.push_thread.start()
        
        logger.info(f"Web服务器已启动，访问地址: http://0.0.0.0:{SYSTEM_CONFIG['WEB_PORT']}")
    
    def stop(self):
        """停止Web服务器"""
        logger.info("正在停止Web服务器...")
        self.running = False
        
        # 等待线程结束
        if self.push_thread and self.push_thread.is_alive():
            self.push_thread.join(timeout=2.0)
        
        # Flask没有优雅的停止方法，只能依赖线程结束
        # 实际生产环境应使用更健壮的Web服务器如Gunicorn
        
        logger.info("Web服务器已停止")
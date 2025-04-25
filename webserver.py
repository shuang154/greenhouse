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

# 导入配置文件 - 修复导入错误
from config import SYSTEM_CONFIG

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
    
    def __init__(self, sensor_module, controller_module):
        """初始化Web服务器"""
        logger.info("初始化Web服务器...")
        
        # 保存传感器和控制器模块引用
        self.sensor_module = sensor_module
        self.controller_module = controller_module
        
        # 创建Flask应用
        self.app = Flask(__name__)
        
        # 设置路由
        self._setup_routes()
        
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
                
            return render_template('dashboard.html', server_ip=ip, server_port=SYSTEM_CONFIG["WEB_PORT"])
        
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
    def _run_server(self):
        """在线程中运行Flask服务器"""
        try:
            self.app.run(
                host='0.0.0.0',
                port=SYSTEM_CONFIG["WEB_PORT"],
                debug=False,
                use_reloader=False,
                threaded=True
            )
        except Exception as e:
            logger.error(f"Web服务器运行错误: {e}")
        
    def start(self):
        """启动Web服务器"""
        if self.running:
            logger.warning("Web服务器已在运行中")
            return
        
        self.running = True
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        logger.info(f"Web服务器已启动，访问地址: http://0.0.0.0:{SYSTEM_CONFIG['WEB_PORT']}")
    
    def stop(self):
        """停止Web服务器"""
        logger.info("正在停止Web服务器...")
        self.running = False
        
        # Flask没有优雅的停止方法，只能依赖线程结束
        # 实际生产环境应使用更健壮的Web服务器如Gunicorn
        
        logger.info("Web服务器已停止")

"""
云服务连接模块 - 负责与云服务器的通信
"""

import logging
import threading
import time
import json
import socketio
import ssl
import requests
import uuid
import os

# 导入配置文件
from config import SYSTEM_CONFIG, CLOUD_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(SYSTEM_CONFIG["LOG_FILE"]),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("CloudConnector")

class CloudConnector:
    """云服务连接类"""
    
    def __init__(self, sensor_module, controller_module):
        """初始化云服务连接"""
        logger.info("初始化云服务连接...")
        
        # 保存传感器和控制器模块引用
        self.sensor_module = sensor_module
        self.controller_module = controller_module
        
        # 创建设备ID，如果没有的话
        self.device_id = CLOUD_CONFIG.get("DEVICE_ID")
        if not self.device_id:
            self.device_id = str(uuid.uuid4())
            logger.info(f"生成新的设备ID: {self.device_id}")
            # 这里可以添加保存设备ID的代码
        
        # Socket.IO客户端
        self.sio = socketio.Client()
        
        # 注册事件处理
        self._setup_socketio_handlers()
        
        # 连接状态
        self.connected = False
        
        # 数据推送线程
        self.push_thread = None
        self.running = False
        
        logger.info("云服务连接初始化完成")
    
    def _setup_socketio_handlers(self):
        """设置Socket.IO事件处理器"""
        
        @self.sio.event
        def connect():
            """连接成功事件"""
            logger.info("已连接到云服务器")
            self.connected = True
            
            # 注册设备
            self.sio.emit('register_device', {
                'device_id': self.device_id,
                'device_name': CLOUD_CONFIG.get("DEVICE_NAME", "智能温室"),
                'device_type': 'greenhouse'
            })
        
        @self.sio.event
        def disconnect():
            """连接断开事件"""
            logger.info("与云服务器的连接已断开")
            self.connected = False
            
            # 尝试重新连接
            if self.running:
                time.sleep(5)  # 等待5秒后重试
                self._connect_to_server()
        
        @self.sio.event
        def register_response(data):
            """设备注册响应"""
            if data.get('success'):
                logger.info("设备注册成功")
            else:
                logger.error(f"设备注册失败: {data.get('error')}")
        
        @self.sio.event
        def control_command(data):
            """接收控制命令"""
            logger.info(f"收到云服务器控制命令: {data}")
            
            try:
                command = data.get('command')
                
                if command == 'set_auto_mode':
                    # 设置自动/手动模式
                    auto_mode = data.get('value', True)
                    self.controller_module.set_auto_mode(auto_mode)
                    
                    # 向服务器发送成功响应
                    self.sio.emit('command_result', {
                        'command_id': data.get('command_id'),
                        'success': True,
                        'message': f"自动模式已设为: {'开启' if auto_mode else '关闭'}"
                    })
                    
                elif command == 'control_device':
                    # 控制设备
                    device = data.get('device')
                    action = data.get('action')
                    value = data.get('value')
                    
                    result = self.controller_module.manual_control(device, action, value)
                    
                    if result:
                        self.sio.emit('command_result', {
                            'command_id': data.get('command_id'),
                            'success': True,
                            'message': f"设备 {device} 已成功控制"
                        })
                    else:
                        self.sio.emit('command_result', {
                            'command_id': data.get('command_id'),
                            'success': False,
                            'error': f"控制设备 {device} 失败"
                        })
                    
                else:
                    # 未知命令
                    self.sio.emit('command_result', {
                        'command_id': data.get('command_id'),
                        'success': False,
                        'error': f"未知命令: {command}"
                    })
                
                # 数据变化后立即推送一次最新状态
                self._push_data_to_cloud()
                
            except Exception as e:
                logger.error(f"处理控制命令时出错: {e}")
                
                # 向云服务器发送错误信息
                self.sio.emit('command_result', {
                    'command_id': data.get('command_id'),
                    'success': False,
                    'error': str(e)
                })
    
    def _connect_to_server(self):
        """连接到云服务器"""
        try:
            server_url = CLOUD_CONFIG["SERVER_URL"]
            
            # 创建连接选项
            connection_opts = {}
            
            # 如果有SSL设置
            if CLOUD_CONFIG.get("USE_SSL", True):
                if CLOUD_CONFIG.get("SSL_VERIFY", True):
                    connection_opts = {
                        "ssl_verify": True
                    }
                else:
                    # 禁用SSL验证（仅用于测试）
                    connection_opts = {
                        "ssl_verify": False
                    }
            
            # 连接到服务器
            self.sio.connect(
                server_url,
                **connection_opts
            )
            
            logger.info(f"正在连接到云服务器: {server_url}")
            
        except Exception as e:
            logger.error(f"连接到云服务器失败: {e}")
            self.connected = False
            
            # 等待后重试
            if self.running:
                time.sleep(10)  # 10秒后重试
                self._connect_to_server()
    
    def _push_data_to_cloud(self):
        """推送数据到云服务器"""
        if not self.connected:
            return
        
        try:
            # 获取最新数据
            sensor_data = self.sensor_module.get_latest_readings()
            controller_status = self.controller_module.get_status()
            
            # 构建数据结构
            data = {
                'device_id': self.device_id,
                'timestamp': time.time(),
                'sensors': sensor_data,
                'controllers': controller_status,
                'device_name': CLOUD_CONFIG.get("DEVICE_NAME", "智能温室")
            }
            
            # 发送到云服务器
            self.sio.emit('device_data', data)
            logger.debug("数据已推送到云服务器")
            
        except Exception as e:
            logger.error(f"推送数据到云服务器失败: {e}")
    
    def _data_push_loop(self):
        """数据推送循环"""
        while self.running:
            if self.connected:
                self._push_data_to_cloud()
            time.sleep(CLOUD_CONFIG.get("PUSH_INTERVAL", 5))  # 默认每5秒推送一次
    
    def start(self):
        """启动云服务连接"""
        if self.running:
            logger.warning("云服务连接已在运行中")
            return
        
        self.running = True
        
        # 连接到服务器
        self._connect_to_server()
        
        # 启动数据推送线程
        self.push_thread = threading.Thread(target=self._data_push_loop)
        self.push_thread.daemon = True
        self.push_thread.start()
        
        logger.info("云服务连接已启动")
    
    def stop(self):
        """停止云服务连接"""
        logger.info("正在停止云服务连接...")
        self.running = False
        
        # 等待线程结束
        if self.push_thread and self.push_thread.is_alive():
            self.push_thread.join(timeout=2.0)
        
        # 断开连接
        if self.connected:
            try:
                self.sio.disconnect()
            except:
                pass
        
        logger.info("云服务连接已停止")
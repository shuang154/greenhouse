# cloud_connector.py
import requests
import json
import time
import threading
import subprocess
import logging
import base64
import io
import os
import uuid
from datetime import datetime

# 导入配置文件
from config import CLOUD_CONFIG, SYSTEM_CONFIG

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
    """云服务连接器类"""
    
    def __init__(self, sensor_module, controller_module, camera_module=None):
        """初始化云服务连接器"""
        logger.info("初始化云服务连接器...")
        
        # 保存模块引用
        self.sensor_module = sensor_module
        self.controller_module = controller_module
        self.camera_module = camera_module
        
        # 获取设备ID（如果为空则自动生成）
        self.device_id = CLOUD_CONFIG.get("DEVICE_ID", "")
        if not self.device_id:
            self.device_id = str(uuid.uuid4())
            logger.info(f"已生成新的设备ID: {self.device_id}")
        
        # 云服务器URL
        self.server_url = CLOUD_CONFIG.get("SERVER_URL", "")
        
        # 设置设备名称
        self.device_name = CLOUD_CONFIG.get("DEVICE_NAME", "智能温室")
        
        # 推送间隔（秒）
        self.push_interval = CLOUD_CONFIG.get("PUSH_INTERVAL", 5)
        
        # 摄像头推送间隔（3秒）
        self.camera_push_interval = 3
        
        # 运行状态
        self.running = False
        self.push_thread = None
        
        # 摄像头流配置
        self.enable_camera_stream = camera_module is not None
        self.auth_token = CLOUD_CONFIG.get("AUTH_TOKEN", "")
        
        # 确保临时目录存在
        os.makedirs('/tmp', exist_ok=True)
        
        logger.info("云服务连接器初始化完成")
    
    def start(self):
        """启动数据推送服务"""
        if self.running:
            logger.warning("云服务连接器已在运行中")
            return
        
        # 注册设备
        self._register_device()
        
        # 确保没有其他进程使用摄像头
        self._cleanup_camera_processes()
        
        # 启动数据推送线程
        self.running = True
        self.push_thread = threading.Thread(target=self._push_data_loop)
        self.push_thread.daemon = True
        self.push_thread.start()
        
        logger.info("云服务连接器已启动")
    
    def _cleanup_camera_processes(self):
        """清理可能存在的摄像头进程"""
        try:
            subprocess.run(['pkill', '-f', 'raspistill'], check=False)
            time.sleep(0.5)  # 等待进程停止
        except Exception as e:
            logger.debug(f"清理摄像头进程时出错: {e}")
    
    def _register_device(self):
        """向云服务器注册设备"""
        try:
            # 构建注册数据
            register_data = {
                "device_id": self.device_id,
                "device_name": self.device_name,
                "device_type": "greenhouse",
                "capabilities": {
                    "sensors": [
                        "air_temperature", "air_humidity", "soil_moisture", 
                        "soil_temperature", "light_intensity"
                    ],
                    "actuators": ["fan", "servo"],
                    "has_camera": self.enable_camera_stream
                }
            }
            
            # 发送注册请求
            response = requests.post(
                f"{self.server_url}/api/devices/register",
                json=register_data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("设备注册成功")
                return True
            else:
                logger.error(f"设备注册失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"设备注册发生错误: {e}")
            return False
    
    def _push_data_loop(self):
        """数据推送循环"""
        last_camera_push = 0
        last_command_check = 0
        connection_retry_count = 0
        
        while self.running:
            try:
                # 获取传感器数据
                sensor_data = self.sensor_module.get_latest_readings()
                if 'soil_moisture' in sensor_data:
                    sensor_data['soil_moisture'] = 100 - sensor_data['soil_moisture']
                
                # 获取控制器状态
                controller_status = self.controller_module.get_status()
                
                # 构建推送数据
                push_data = {
                    "device_id": self.device_id,
                    "timestamp": datetime.now().isoformat(),
                    "sensors": sensor_data,
                    "controller": controller_status
                }
                
                # 发送数据到云服务器
                response = requests.post(
                    f"{self.server_url}/api/data/push",
                    json=push_data,
                    timeout=5
                )
                
                if response.status_code == 200:
                    logger.debug("数据推送成功")
                    connection_retry_count = 0  # 重置重试计数
                else:
                    logger.warning(f"数据推送失败: {response.status_code} - {response.text}")
                
                # 每3秒推送一次摄像头图像
                current_time = time.time()
                if self.enable_camera_stream and (current_time - last_camera_push) >= self.camera_push_interval:
                    self._push_camera_image()
                    last_camera_push = current_time
                
                # 每5秒检查一次控制命令
                if (current_time - last_command_check) >= 5:
                    self._check_control_commands()
                    last_command_check = current_time
                
                # 等待下一次推送
                time.sleep(self.push_interval)
                
            except Exception as e:
                logger.error(f"数据推送循环异常: {e}")
                connection_retry_count += 1
                # 根据连续失败次数调整等待时间（指数退避）
                retry_delay = min(30, self.push_interval * (2 ** min(connection_retry_count, 5)))
                logger.info(f"将在 {retry_delay} 秒后重试连接 (尝试次数: {connection_retry_count})")
                time.sleep(retry_delay)
    


    def _push_camera_image(self):
        """使用libcamera推送摄像头图像到云服务器"""
        try:
            logger.debug("开始推送摄像头图像...")
            
            # 方案1：完全控制库加载路径
            env = os.environ.copy()
            # 清空LD_LIBRARY_PATH
            env.pop('LD_LIBRARY_PATH', None)
            # 明确设置库搜索路径，只使用包含新版本的目录
            env['LD_LIBRARY_PATH'] = '/usr/lib/aarch64-linux-gnu'
            
            # 使用libcamera-still捕获图像
            start_time = time.time()
            cmd = ['/usr/bin/libcamera-still', '-o', '/tmp/camera_frame.jpg', '--width', '640', '--height', '480', '-n', '--timeout', '100']
            
            logger.debug(f"执行命令: {' '.join(cmd)}")
            logger.debug(f"环境变量: LD_LIBRARY_PATH={env.get('LD_LIBRARY_PATH')}")
            logger.debug(f"环境变量: LD_PRELOAD={env.get('LD_PRELOAD')}")
            
            # 使用修改后的环境运行命令
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)
            
            if result.returncode != 0:
                logger.error(f"libcamera-still命令执行失败: {result.stderr}")
                return False
                
            # 检查文件是否创建
            if not os.path.exists('/tmp/camera_frame.jpg'):
                logger.error("图像文件未创建")
                return False
                
            # 检查文件大小
            file_size = os.path.getsize('/tmp/camera_frame.jpg')
            logger.debug(f"图像文件大小: {file_size} 字节")
            
            # 读取图像文件
            with open('/tmp/camera_frame.jpg', 'rb') as f:
                image_data = f.read()
            
            # 发送到服务器
            headers = {
                'Device-ID': self.device_id,
                'Content-Type': 'image/jpeg',
                'Timestamp': datetime.now().isoformat()
            }
            
            if self.auth_token:
                headers['Auth-Token'] = self.auth_token
                
            url = f"{self.server_url}/api/camera/frame-push"
            logger.info(f"推送图像到: {url}, 设备ID: {self.device_id}")
            logger.debug(f"请求头: {headers}")
            
            try:
                response = requests.post(
                    url,
                    data=image_data,
                    headers=headers,
                    timeout=10
                )
                
                logger.info(f"服务器响应状态码: {response.status_code}")
                logger.debug(f"服务器响应内容: {response.text}")
                
                if response.status_code == 200:
                    # 计算帧率
                    elapsed = time.time() - start_time
                    fps = 1 / elapsed if elapsed > 0 else 0
                    logger.info(f"图像推送成功 (FPS: {fps:.1f})")
                    return True
                else:
                    logger.warning(f"图像推送失败: {response.status_code} - {response.text}")
                    return False
                    
            except requests.exceptions.Timeout:
                logger.error("请求超时，服务器可能无法访问")
                return False
            except requests.exceptions.ConnectionError:
                logger.error("连接错误，请检查网络和服务器URL")
                return False
            except Exception as e:
                logger.error(f"HTTP请求异常: {e}")
                return False
                
        except Exception as e:
            logger.error(f"推送摄像头图像错误: {e}")
            return False
                
                
    def _push_camera_image_fallback(self):
        """备用摄像头图像推送方法"""
        try:
            # 如果有测试图像，可以提交那个文件
            test_image_path = '/tmp/test_image.jpg'
            if os.path.exists(test_image_path):
                with open(test_image_path, 'rb') as f:
                    frame_data = f.read()
                
                frame_base64 = base64.b64encode(frame_data).decode('utf-8')
                
                # 构建图像数据
                image_data = {
                    "device_id": self.device_id,
                    "timestamp": datetime.now().isoformat(),
                    "image": frame_base64,
                    "format": "jpeg"
                }
                
                # 发送图像数据
                response = requests.post(
                    f"{self.server_url}/api/camera/push",
                    json=image_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    logger.debug("备用图像推送成功")
                    return True
                else:
                    logger.warning(f"备用图像推送失败: {response.status_code} - {response.text}")
                    return False
            else:
                logger.debug("没有可用的备用图像")
                return False
                
        except Exception as e:
            logger.error(f"备用图像推送错误: {e}")
            return False
    
    def _check_control_commands(self):
        """检查并处理云服务器发送的控制命令"""
        try:
            # 获取待处理的控制命令
            response = requests.get(
                f"{self.server_url}/api/devices/{self.device_id}/commands",
                timeout=5
            )
            
            if response.status_code != 200:
                return
            
            commands = response.json()
            if not commands or len(commands) == 0:
                return
            
            for command in commands:
                cmd_type = command.get('command')
                cmd_data = command.get('data')
                
                logger.info(f"收到云端控制命令: {cmd_type}")
                
                if cmd_type == 'mode':
                    auto_mode = cmd_data.get('auto_mode', True)
                    self.controller_module.set_auto_mode(auto_mode)
                    logger.info(f"已设置模式为: {'自动' if auto_mode else '手动'}")
                    
                elif cmd_type == 'fan':
                    state = cmd_data.get('state', False)
                    action = 'on' if state else 'off'
                    self.controller_module.manual_control('fan', action)
                    logger.info(f"已设置风扇为: {'开启' if state else '关闭'}")
                    
                elif cmd_type == 'pump':
                    # 如果有水泵控制，则处理
                    pass
                    
                elif cmd_type == 'light':
                    # 如果有灯光控制，则处理
                    pass
                    
                elif cmd_type == 'stepper':
                    position = cmd_data.get('position', 0)
                    self.controller_module.manual_control('stepper', 'set', position)
                    logger.info(f"已设置窗口开度为: {position}%")
                    
                elif cmd_type == 'thresholds':
                    # 更新阈值设置（需要增加相关功能）
                    logger.info(f"收到阈值更新: {cmd_data}")
                    
            # 确认已处理的命令
            commands_to_confirm = [cmd.get('id') for cmd in commands if 'id' in cmd]
            if commands_to_confirm:
                try:
                    confirm_response = requests.post(
                        f"{self.server_url}/api/devices/{self.device_id}/commands/confirm",
                        json={"command_ids": commands_to_confirm},
                        timeout=5
                    )
                    
                    if confirm_response.status_code == 200:
                        logger.debug("命令确认成功")
                    else:
                        logger.warning(f"命令确认失败: {confirm_response.status_code} - {confirm_response.text}")
                
                except Exception as e:
                    logger.error(f"确认命令时发生错误: {e}")
            
        except Exception as e:
            logger.error(f"检查控制命令时发生错误: {e}")
    
    def stop(self):
        """停止数据推送服务"""
        logger.info("正在停止云服务连接器...")
        self.running = False
        
        # 清理摄像头进程
        self._cleanup_camera_processes()
        
        if self.push_thread and self.push_thread.is_alive():
            self.push_thread.join(timeout=5.0)
        
        logger.info("云服务连接器已停止")
"""
摄像头模块 - 使用picamera2控制CSI摄像头
"""

import io
import logging
import threading
import time
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

# 导入配置文件
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

logger = logging.getLogger("CameraModule")

class CameraModule:
    """摄像头模块类"""
    
    def __init__(self):
        """初始化摄像头模块"""
        logger.info("初始化摄像头模块...")
        
        self.camera = None
        self.encoder = None
        self.stream_thread = None
        self.frame_buffer = io.BytesIO()
        self.frame_lock = threading.Lock()
        self.running = False
        
        try:
            # 初始化摄像头
            self.camera = Picamera2()
            
            # 获取可用的配置并打印日志
            camera_configs = self.camera.sensor_modes
            logger.info(f"摄像头支持的模式: {camera_configs}")
            
            # 配置摄像头 - 使用更简单的配置
            width, height = SYSTEM_CONFIG["CAMERA_RESOLUTION"]
            self.camera.configure(self.camera.create_preview_configuration(
                main={"size": (width, height), "format": "RGB888"},
                lores={"size": (width // 2, height // 2), "format": "YUV420"},
                display="lores"
            ))
            
            logger.info("摄像头模块初始化成功")
        except Exception as e:
            logger.error(f"摄像头模块初始化失败: {e}")
            if self.camera:
                try:
                    self.camera.close()
                except:
                    pass
                self.camera = None
    
    def start(self):
        """启动摄像头并开始视频流"""
        if not self.camera:
            logger.error("摄像头未初始化，无法启动")
            return False
        
        if self.running:
            logger.warning("摄像头已在运行中")
            return True
        
        try:
            # 启动摄像头
            self.camera.start()
            self.running = True
            
            # 启动视频流线程
            self.stream_thread = threading.Thread(target=self._stream_loop)
            self.stream_thread.daemon = True
            self.stream_thread.start()
            
            logger.info("摄像头已启动")
            return True
        except Exception as e:
            logger.error(f"启动摄像头失败: {e}")
            self.cleanup()
            return False
    
    def _stream_loop(self):
        """视频流循环"""
        while self.running:
            try:
                # 捕获一帧
                frame = self.camera.capture_array()
                
                # 将RGB帧转换为JPEG
                from PIL import Image
                image = Image.fromarray(frame)
                
                # 安全地更新帧缓冲区
                with self.frame_lock:
                    self.frame_buffer.seek(0)
                    self.frame_buffer.truncate()
                    image.save(self.frame_buffer, format="JPEG", quality=85)
                
                # 控制帧率
                time.sleep(1.0 / SYSTEM_CONFIG["CAMERA_FRAMERATE"])
            except Exception as e:
                logger.error(f"视频流循环异常: {e}")
                time.sleep(1)  # 出错后等待1秒再尝试
    
    def get_frame(self):
        """获取当前帧的JPEG数据"""
        if not self.running:
            return None
        
        try:
            # 安全地获取当前帧的副本
            with self.frame_lock:
                frame_data = self.frame_buffer.getvalue()
            
            return frame_data
        except Exception as e:
            logger.error(f"获取视频帧失败: {e}")
            return None
    
    def cleanup(self):
        """清理资源"""
        logger.info("正在清理摄像头模块资源...")
        self.running = False
        
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2.0)
        
        if self.camera:
            try:
                self.camera.stop()
                self.camera.close()
            except Exception as e:
                logger.error(f"关闭摄像头时出错: {e}")
            self.camera = None
        
        logger.info("摄像头模块资源已清理")
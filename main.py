#!/usr/bin/env python3


import time
import logging
import signal
import sys
import os
from pathlib import Path

# 确保目录结构存在
project_root = Path(os.path.dirname(os.path.realpath(__file__)))
logs_dir = project_root / "logs"
data_dir = project_root / "data"

logs_dir.mkdir(exist_ok=True)
data_dir.mkdir(exist_ok=True)

# 导入配置
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

logger = logging.getLogger("Main")

# 导入模块
from sensors import SensorModule
from controllers import ControllerModule
from webserver import WebServer

# 全局变量
sensor_module = None
controller_module = None
web_server = None

def signal_handler(sig, frame):
 
    logger.info("收到退出信号，正在关闭系统...")
    
    if web_server:
        web_server.stop()
    
    if controller_module:
        controller_module.cleanup()
    
    if sensor_module:
        sensor_module.cleanup()
    
    logger.info("系统已安全关闭")
    sys.exit(0)

def main():
   
    global sensor_module, controller_module, web_server
    
    logger.info("智能温室监控系统启动中...")
    
    try:
        # 初始化传感器模块
        logger.info("初始化传感器模块...")
        sensor_module = SensorModule()
        
        # 初始化控制器模块
        logger.info("初始化控制器模块...")
        controller_module = ControllerModule(sensor_module)
        
        # 初始化Web服务器
        logger.info("初始化Web服务器...")
        web_server = WebServer(sensor_module, controller_module)
        
        # 启动Web服务器
        web_server.start()
        
        logger.info(f"系统启动完成，Web界面可通过 http://localhost:{SYSTEM_CONFIG['WEB_PORT']} 访问")
        logger.info("使用Ctrl+C退出系统")
        
        # 注册信号处理
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 保持主线程运行
        while True:
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"系统启动失败: {e}")
        
        # 清理资源
        if web_server:
            web_server.stop()
        
        if controller_module:
            controller_module.cleanup()
        
        if sensor_module:
            sensor_module.cleanup()
        
        sys.exit(1)

if __name__ == "__main__":
    main()
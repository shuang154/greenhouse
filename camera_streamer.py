# camera_streamer.py - 添加到您的树莓派项目中
import time
import threading
import requests
import subprocess
import io
import os
from datetime import datetime

# 全局变量
server_url = "http://47.93.80.194/api/camera/frame-push"  # 修改为您的服务器地址
device_id = "您的设备ID"  # 填入您的设备ID
auth_token = "您的认证令牌"  # 安全认证
streaming = False
stream_thread = None

def capture_and_send_frames():
    global streaming
    
    print("开始图像流传输...")
    
    while streaming:
        try:
            # 使用raspistill捕获单帧图像
            start_time = time.time()
            #cmd = ['raspistill', '-w', '640', '-h', '480', '-q', '30', '-o', '/tmp/camera_frame.jpg', '-n', '-t', '1']
            subprocess.call(cmd)
            
            # 读取图像并发送
            with open('/tmp/camera_frame.jpg', 'rb') as f:
                image_data = f.read()
            
            # 发送到服务器 - 使用二进制数据，不用base64
            headers = {
                'Device-ID': device_id,
                'Auth-Token': auth_token,
                'Content-Type': 'image/jpeg',
                'Timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(
                server_url,
                data=image_data,
                headers=headers,
                timeout=2.0  # 设置超时避免阻塞
            )
            
            # 检查响应
            if response.status_code == 200:
                # 计算帧率
                elapsed = time.time() - start_time
                fps = 1 / elapsed if elapsed > 0 else 0
                
                if fps < 8:  # 如果帧率过低，输出警告
                    print(f"警告：帧率较低 ({fps:.1f} FPS)，可能影响流畅度")
                
                # 根据帧率调整等待时间
                target_fps = 10  # 目标帧率
                wait_time = max(0, (1/target_fps) - elapsed)
                time.sleep(wait_time)
            else:
                print(f"服务器返回错误: {response.status_code}")
                time.sleep(1)  # 错误后等待时间
                
        except Exception as e:
            print(f"发送图像帧时出错: {e}")
            time.sleep(2)  # 出错后等待时间
    
    print("图像流传输已停止")

def start_streaming():
    global streaming, stream_thread
    
    if streaming:
        return
    
    streaming = True
    stream_thread = threading.Thread(target=capture_and_send_frames)
    stream_thread.daemon = True
    stream_thread.start()

def stop_streaming():
    global streaming
    streaming = False
    # 线程将自行终止

# 此函数可以从您的main.py调用
def initialize_camera_stream():
    start_streaming()
    return True
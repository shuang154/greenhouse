#!/usr/bin/env python3
"""
测试不同的摄像头初始化方法
"""

import sys
import os

# 方法1：使用虚拟环境的picamera2
print("=== 方法1：使用虚拟环境的Picamera2 ===")
try:
    import picamera2
    print(f"Picamera2版本: {getattr(picamera2, '__version__', '版本未知')}")
    
    from picamera2 import Picamera2
    cameras = Picamera2.global_camera_info()
    print(f"发现摄像头: {len(cameras)} 个")
    
    if len(cameras) > 0:
        print(f"摄像头信息: {cameras[0]}")
    else:
        print("未发现摄像头")
except Exception as e:
    print(f"错误: {e}")

# 方法2：使用系统Python的picamera2
print("\n=== 方法2：使用系统Python的Picamera2 ===")
print("退出虚拟环境并运行: python3 -c \"import picamera2; print(picamera2.__version__)\"")

# 方法3：直接使用libcamera
print("\n=== 方法3：使用libcamera命令 ===")
os.system("libcamera-hello --list-cameras")

# 方法4：检查DMA相关设置
print("\n=== 方法4：检查DMA设置 ===")
print("检查 /sys/module/dma_buf/parameters/:")
try:
    import glob
    dma_params = glob.glob('/sys/module/dma_buf/parameters/*')
    if dma_params:
        for param in dma_params:
            try:
                with open(param, 'r') as f:
                    value = f.read().strip()
                print(f"  {os.path.basename(param)}: {value}")
            except:
                print(f"  {os.path.basename(param)}: 无法读取")
    else:
        print("  没有找到DMA参数")
except Exception as e:
    print(f"错误: {e}")

# 方法5：检查v4l2设备
print("\n=== 方法5：检查v4l2设备 ===")
os.system("v4l2-ctl --list-devices")

print("\n=== 建议 ===")
print("如果虚拟环境的picamera2不工作，请:")
print("1. 使用系统Python:")
print("   deactivate")
print("   python3 your_script.py")
print("2. 或者，安装系统的picamera2到虚拟环境:")
print("   pip uninstall picamera2")
print("   pip install picamera2 --system-site-packages")
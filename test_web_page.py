#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# test_web_page_simple.py
import requests
import sys
import socket
import time

def check_server_running():
    """检查服务是否运行"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('127.0.0.1', 8000))
        s.close()
        return result == 0
    except:
        return False

def check_web_page():
    """检查网页能否访问"""
    print("=== 网页访问测试 ===")
    
    # 检查服务是否运行
    if not check_server_running():
        print("ERROR: 服务器在8000端口未运行！")
        print("尝试运行: python main.py")
        return
    
    print("✓ 服务器运行正常")
    
    try:
        # 测试根路径
        response = requests.get('http://127.0.0.1:8000/', timeout=5)
        print(f"HTTP状态码: {response.status_code}")
        print(f"响应头部: {dict(response.headers)}")
        print(f"响应长度: {len(response.content)} bytes")
        
        # 保存响应到文件
        with open('/tmp/web_response.html', 'wb') as f:
            f.write(response.content)
        print("响应已保存到 /tmp/web_response.html")
        
        # 显示前500字符
        try:
            text = response.content.decode('utf-8')
            print("\n响应内容（前500字符）：")
            print(text[:500])
        except:
            print("无法以UTF-8解码响应")
            
    except Exception as e:
        print(f"ERROR: {e}")

def check_processes():
    """检查进程"""
    print("\n=== 进程检查 ===")
    try:
        import subprocess
        # 查找Python进程运行Web服务器
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        web_processes = [line for line in lines if 'python' in line and ('main.py' in line or 'webserver' in line)]
        
        if web_processes:
            print("发现Web相关进程：")
            for process in web_processes:
                print(process)
        else:
            print("未找到Web相关进程")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    check_web_page()
    check_processes()
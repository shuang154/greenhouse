# test_socketio.py
from flask import Flask
from flask_socketio import SocketIO, emit
import time
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Socket.IO Test</title>
        <script src="https://cdn.jsdelivr.net/npm/socket.io/client-dist/socket.io.min.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const socket = io();
                socket.on('connect', function() {
                    document.getElementById('status').textContent = '已连接';
                    document.getElementById('status').style.color = 'green';
                });
                socket.on('disconnect', function() {
                    document.getElementById('status').textContent = '已断开';
                    document.getElementById('status').style.color = 'red';
                });
                socket.on('test_message', function(data) {
                    const messagesDiv = document.getElementById('messages');
                    messagesDiv.innerHTML += '<p>' + JSON.stringify(data) + '</p>';
                });
            });
        </script>
    </head>
    <body>
        <h1>Socket.IO连接测试</h1>
        <p>连接状态: <span id="status">等待连接...</span></p>
        <div id="messages"></div>
    </body>
    </html>
    """

def send_test_data():
    count = 0
    while True:
        count += 1
        socketio.emit('test_message', {'count': count, 'time': time.strftime('%H:%M:%S')})
        print(f"已发送测试数据: {count}")
        time.sleep(1)

@socketio.on('connect')
def handle_connect():
    print('客户端已连接')

if __name__ == '__main__':
    threading.Thread(target=send_test_data, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=8000, debug=False)

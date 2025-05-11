/**
 * 树莓派智能温室客户端
 * 读取真实传感器和摄像头数据，发送到云服务器
 */

const io = require('socket.io-client');
const Gpio = require('onoff').Gpio;
const dht = require('node-dht-sensor').promises;
const PiCamera = require('pi-camera');

// 服务器连接配置
const SERVER_URL = 'http://47.93.80.194:3000'; // 阿里云服务器地址
const DEVICE_ID = 'raspberry-device-1';
const DEVICE_NAME = '树莓派温室';

// 传感器配置（参考您的 config.py）
const GPIO_CONFIG = {
  DHT11_PIN: 4,          // DHT11 温湿度传感器
  SOIL_MOISTURE_PIN: 17, // 土壤湿度传感器
  RELAY_FAN: 18,         // 风扇继电器
  SERVO_PIN: 12          // 舵机（PWM）
};

// 初始化 GPIO
const soilMoistureSensor = new Gpio(GPIO_CONFIG.SOIL_MOISTURE_PIN, 'in');
const fanRelay = new Gpio(GPIO_CONFIG.RELAY_FAN, 'out');
const servo = new Gpio(GPIO_CONFIG.SERVO_PIN, 'out');

// 摄像头配置
const camera = new PiCamera({
  mode: 'photo',
  width: 640,
  height: 480,
  nopreview: true,
  output: `${__dirname}/capture.jpg`
});

// WebSocket 连接
console.log(`正在连接到服务器 ${SERVER_URL}...`);
const socket = io(SERVER_URL, {
  transports: ['websocket', 'polling'],
  reconnectionAttempts: 10,
  reconnectionDelay: 2000,
  timeout: 10000
});

// 设备状态
let deviceState = {
  sensors: {
    air_temperature: 0,
    air_humidity: 0,
    soil_moisture: 0,
    light_intensity: 0 // 暂未实现光照传感器
  },
  controllers: {
    auto_mode: true,
    fan_status: false,
    servo_angle: 0
  }
};

// 连接事件处理
socket.on('connect', () => {
  console.log('已连接到服务器，socket ID:', socket.id);
  registerDevice();
});

socket.on('connect_error', (error) => {
  console.error('连接错误:', error.message);
});

socket.on('disconnect', () => {
  console.log('与服务器的连接已断开');
});

socket.on('register_response', (response) => {
  console.log('设备注册响应:', response);
  if (response.success) {
    console.log('设备注册成功，开始发送数据...');
    startSendingData();
    startCameraStream();
  } else {
    console.error('设备注册失败:', response.error);
  }
});

socket.on('control_command', (command) => {
  console.log('收到控制命令:', command);
  let result = { command_id: command.command_id, success: true };

  switch (command.command) {
    case 'set_auto_mode':
      deviceState.controllers.auto_mode = command.value;
      console.log(`设置自动模式: ${command.value ? '开启' : '关闭'}`);
      break;
    case 'control_device':
      if (command.device === 'fan') {
        const status = command.action === 'on';
        fanRelay.writeSync(status ? 0 : 1); // 低电平触发
        deviceState.controllers.fan_status = status;
        console.log(`控制风扇: ${command.action}`);
      } else if (command.device === 'servo') {
        const angle = parseInt(command.value, 10);
        setServoAngle(angle);
        deviceState.controllers.servo_angle = angle;
        console.log(`设置舵机角度: ${angle}°`);
      } else {
        result.success = false;
        result.error = '不支持的设备';
      }
      break;
    default:
      result.success = false;
      result.error = '未知命令';
  }

  socket.emit('command_result', result);
  sendDeviceData();
});

// 注册设备
function registerDevice() {
  socket.emit('register_device', {
    device_id: DEVICE_ID,
    device_name: DEVICE_NAME,
    device_type: '智能温室'
  });
}

// 读取传感器数据
async function readSensors() {
  try {
    // 读取 DHT11 温湿度
    const dhtData = await dht.read(11, GPIO_CONFIG.DHT11_PIN);
    deviceState.sensors.air_temperature = dhtData.temperature;
    deviceState.sensors.air_humidity = dhtData.humidity;

    // 读取土壤湿度（假设高电平表示干燥）
    const soilValue = soilMoistureSensor.readSync();
    deviceState.sensors.soil_moisture = soilValue ? 20 : 80; // 简单映射，需校准

    // 光照传感器（暂未实现，保留模拟值）
    deviceState.sensors.light_intensity = deviceState.sensors.light_intensity || 5000;
  } catch (error) {
    console.error('传感器读取错误:', error);
  }
}

// 设置舵机角度（简化的 PWM 控制）
function setServoAngle(angle) {
  // 假设使用 PWM 控制舵机，需根据硬件调整
  console.log(`模拟设置舵机角度: ${angle}°`);
  // 实际硬件控制代码需根据您的舵机型号实现
}

// 发送设备数据
function sendDeviceData() {
  const data = {
    device_id: DEVICE_ID,
    device_name: DEVICE_NAME,
    sensors: { ...deviceState.sensors },
    controllers: { ...deviceState.controllers },
    timestamp: Date.now()
  };
  socket.emit('device_data', data);
  console.log('已发送设备数据:', new Date().toLocaleTimeString());
}

// 摄像头数据流
async function startCameraStream() {
  setInterval(async () => {
    try {
      await camera.snap();
      const imageData = require('fs').readFileSync(`${__dirname}/capture.jpg`);
      socket.emit('camera_data', {
        device_id: DEVICE_ID,
        image_data: imageData.toString('base64'),
        timestamp: Date.now()
      });
      console.log('已发送摄像头图像');
    } catch (error) {
      console.error('摄像头捕获失败:', error);
    }
  }, 10000); // 每10秒发送一次
}

// 定期发送数据
async function startSendingData() {
  await readSensors();
  sendDeviceData();
  setInterval(async () => {
    await readSensors();
    sendDeviceData();
  }, 5000); // 每5秒发送一次
}

// 优雅退出
process.on('SIGINT', () => {
  console.log('正在断开连接...');
  soilMoistureSensor.unexport();
  fanRelay.unexport();
  servo.unexport();
  socket.disconnect();
  process.exit();
});

console.log('树莓派客户端已启动，按 Ctrl+C 退出');

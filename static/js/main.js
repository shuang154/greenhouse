/**
 * 智能农业大棚系统 - 前端JavaScript
 */

// 全局变量
let socket;
let temperatureChart;
let humidityChart;
let soilChart;
let lightChart;
let isConnected = false;

// 当文档加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化WebSocket连接
    initWebSocket();
    
    // 初始化图表
    initCharts();
    
    // 初始化事件监听器
    initEventListeners();
    
    // 导航栏活动状态控制
    initNavigation();
    
    console.log('智能农业大棚监控系统已初始化');
});

/**
 * 初始化WebSocket连接
 */
function initWebSocket() {
    // 获取当前页面URL作为WebSocket连接的基础
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}`;
    
    // 创建Socket.IO连接
    socket = io(wsUrl);
    
    // 连接成功事件
    socket.on('connect', function() {
        console.log('已连接到服务器');
        isConnected = true;
        updateConnectionStatus(true);
    });
    
    // 连接断开事件
    socket.on('disconnect', function() {
        console.log('与服务器的连接已断开');
        isConnected = false;
        updateConnectionStatus(false);
    });
    
    // 连接错误事件
    socket.on('connect_error', function(error) {
        console.error('连接错误:', error);
        isConnected = false;
        updateConnectionStatus(false);
    });
    
    // 监听状态更新事件
    socket.on('status_update', function(data) {
        console.log('收到状态更新:', data);
        updateDashboard(data);
        updateControlPanel(data);
        updateCharts(data);
        updateThresholdForm(data);
    });
}

/**
 * 更新连接状态显示
 */
function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('connection-status');
    
    if (connected) {
        statusElement.innerHTML = '<i class="bi bi-check-circle"></i> 已连接到服务器';
        statusElement.classList.remove('alert-info', 'disconnected');
        statusElement.classList.add('connected');
    } else {
        statusElement.innerHTML = '<i class="bi bi-exclamation-triangle"></i> 与服务器的连接已断开，尝试重新连接...';
        statusElement.classList.remove('alert-info', 'connected');
        statusElement.classList.add('disconnected');
    }
}

/**
 * 初始化页面图表
 */
function initCharts() {
    // 温度图表
    const temperatureCtx = document.getElementById('temperature-chart').getContext('2d');
    temperatureChart = new Chart(temperatureCtx, {
        type: 'line',
        data: {
            labels: [], // 时间标签
            datasets: [
                {
                    label: '空气温度 (°C)',
                    data: [],
                    borderColor: 'rgba(13, 110, 253, 1)',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: '土壤温度 (°C)',
                    data: [],
                    borderColor: 'rgba(220, 53, 69, 1)',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: '温度 (°C)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '时间'
                    }
                }
            }
        }
    });
    
    // 湿度图表
    const humidityCtx = document.getElementById('humidity-chart').getContext('2d');
    humidityChart = new Chart(humidityCtx, {
        type: 'line',
        data: {
            labels: [], // 时间标签
            datasets: [{
                label: '空气湿度 (%)',
                data: [],
                borderColor: 'rgba(25, 135, 84, 1)',
                backgroundColor: 'rgba(25, 135, 84, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    max: 100,
                    title: {
                        display: true,
                        text: '湿度 (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '时间'
                    }
                }
            }
        }
    });
    
    // 土壤湿度图表
    const soilCtx = document.getElementById('soil-chart').getContext('2d');
    soilChart = new Chart(soilCtx, {
        type: 'line',
        data: {
            labels: [], // 时间标签
            datasets: [{
                label: '土壤湿度 (%)',
                data: [],
                borderColor: 'rgba(13, 202, 240, 1)',
                backgroundColor: 'rgba(13, 202, 240, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    max: 100,
                    title: {
                        display: true,
                        text: '土壤湿度 (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '时间'
                    }
                }
            }
        }
    });
    
    // 光照强度图表
    const lightCtx = document.getElementById('light-chart').getContext('2d');
    lightChart = new Chart(lightCtx, {
        type: 'line',
        data: {
            labels: [], // 时间标签
            datasets: [{
                label: '光照强度 (lux)',
                data: [],
                borderColor: 'rgba(255, 193, 7, 1)',
                backgroundColor: 'rgba(255, 193, 7, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '光照强度 (lux)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '时间'
                    }
                }
            }
        }
    });
    
    // 获取历史数据填充图表
    fetchHistoricalData();
}

/**
 * 获取历史数据
 */
function fetchHistoricalData() {
    fetch('/api/history?hours=24')
        .then(response => response.json())
        .then(data => {
            if (data && data.length > 0) {
                updateChartsWithHistoricalData(data);
            }
        })
        .catch(error => {
            console.error('获取历史数据失败:', error);
        });
}

/**
 * 使用历史数据更新图表
 */
function updateChartsWithHistoricalData(data) {
    // 准备数据数组
    const labels = [];
    const airTempData = [];
    const soilTempData = [];
    const airHumidityData = [];
    const soilMoistureData = [];
    const lightIntensityData = [];
    
    // 处理数据
    data.forEach(entry => {
        const date = new Date(entry.timestamp);
        const timeLabel = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        labels.push(timeLabel);
        airTempData.push(entry.air_temperature);
        soilTempData.push(entry.soil_temperature);
        airHumidityData.push(entry.air_humidity);
        soilMoistureData.push(entry.soil_moisture);
        lightIntensityData.push(entry.light_intensity);
    });
    
    // 更新温度图表
    temperatureChart.data.labels = labels;
    temperatureChart.data.datasets[0].data = airTempData;
    temperatureChart.data.datasets[1].data = soilTempData;
    temperatureChart.update();
    
    // 更新湿度图表
    humidityChart.data.labels = labels;
    humidityChart.data.datasets[0].data = airHumidityData;
    humidityChart.update();
    
    // 更新土壤湿度图表
    soilChart.data.labels = labels;
    soilChart.data.datasets[0].data = soilMoistureData;
    soilChart.update();
    
    // 更新光照强度图表
    lightChart.data.labels = labels;
    lightChart.data.datasets[0].data = lightIntensityData;
    lightChart.update();
}

/**
 * 初始化事件监听器
 */
function initEventListeners() {
    // 自动/手动模式切换
    const autoModeSwitch = document.getElementById('auto-mode-switch');
    autoModeSwitch.addEventListener('change', function() {
        if (isConnected) {
            const autoMode = this.checked;
            socket.emit('control_mode', { auto_mode: autoMode });
            
            // 更新UI状态
            document.getElementById('auto-mode-label').textContent = autoMode ? '自动模式' : '手动模式';
            
            // 在手动模式下启用控制按钮，自动模式下禁用
            toggleControlsEnabled(!autoMode);
        }
    });
    
    // 风扇控制
    const fanSwitch = document.getElementById('fan-switch');
    fanSwitch.addEventListener('change', function() {
        if (isConnected) {
            const state = this.checked;
            socket.emit('control_fan', { state: state });
        }
    });
    
    // 水泵控制
    const pumpSwitch = document.getElementById('pump-switch');
    pumpSwitch.addEventListener('change', function() {
        if (isConnected) {
            const state = this.checked;
            socket.emit('control_pump', { state: state });
        }
    });
    
    // 灯光控制
    const lightSwitch = document.getElementById('light-switch');
    lightSwitch.addEventListener('change', function() {
        if (isConnected) {
            const state = this.checked;
            socket.emit('control_light', { state: state });
        }
    });
    
    // 步进电机滑块显示值更新
    const stepperRange = document.getElementById('stepper-range');
    const stepperValue = document.getElementById('stepper-value');
    
    stepperRange.addEventListener('input', function() {
        stepperValue.textContent = this.value;
    });
    
    // 步进电机应用按钮
    const stepperApplyBtn = document.getElementById('stepper-apply');
    stepperApplyBtn.addEventListener('click', function() {
        if (isConnected) {
            const position = parseInt(stepperRange.value);
            socket.emit('control_stepper', { position: position });
        }
    });
    
    // 阈值设置表单提交
    const thresholdsForm = document.getElementById('thresholds-form');
    thresholdsForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (isConnected) {
            const thresholds = {
                temp_min: parseFloat(document.getElementById('temp-min').value),
                temp_max: parseFloat(document.getElementById('temp-max').value),
                humidity_min: parseFloat(document.getElementById('humidity-min').value),
                humidity_max: parseFloat(document.getElementById('humidity-max').value),
                soil_moisture_min: parseFloat(document.getElementById('soil-moisture-min').value),
                soil_moisture_max: parseFloat(document.getElementById('soil-moisture-max').value),
                light_min: parseFloat(document.getElementById('light-min').value),
                light_max: parseFloat(document.getElementById('light-max').value)
            };
            
            socket.emit('update_thresholds', thresholds);
            
            alert('阈值设置已保存');
        }
    });
}

/**
 * 初始化导航栏行为
 */
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    // 为导航链接添加点击事件
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 移除所有链接的active类
            navLinks.forEach(link => link.classList.remove('active'));
            
            // 为当前点击的链接添加active类
            this.classList.add('active');
            
            // 获取目标section的ID
            const targetId = this.getAttribute('href').substring(1);
            
            // 滚动到目标section
            document.getElementById(targetId).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
    
    // 滚动时更新导航状态
    window.addEventListener('scroll', function() {
        const scrollPosition = window.scrollY + 100; // 添加一些偏移量
        
        document.querySelectorAll('section').forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            const sectionId = section.getAttribute('id');
            
            if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === `#${sectionId}`) {
                        link.classList.add('active');
                    }
                });
            }
        });
    });
}

/**
 * 根据自动/手动模式切换控制按钮的启用/禁用状态
 */
function toggleControlsEnabled(enabled) {
    const controls = [
        document.getElementById('fan-switch'),
        document.getElementById('pump-switch'),
        document.getElementById('light-switch'),
        document.getElementById('stepper-range'),
        document.getElementById('stepper-apply')
    ];
    
    controls.forEach(control => {
        control.disabled = !enabled;
    });
    
    // 更新提示文本
    const controlCards = document.querySelectorAll('#control .card-body .text-muted');
    
    if (!enabled) {
        controlCards.forEach(card => {
            const originalText = card.dataset.originalText || card.textContent;
            card.dataset.originalText = originalText;
            card.innerHTML = '自动模式下，此控制已禁用。切换到手动模式以启用控制。';
        });
    } else {
        controlCards.forEach(card => {
            if (card.dataset.originalText) {
                card.textContent = card.dataset.originalText;
            }
        });
    }
}

/**
 * 更新仪表盘数据
 */
function updateDashboard(data) {
    if (!data || !data.sensors) return;
    
    const sensors = data.sensors;
    
    // 更新传感器值
    document.getElementById('air-temperature').textContent = sensors.air_temperature.toFixed(1);
    document.getElementById('air-humidity').textContent = sensors.air_humidity.toFixed(1);
    document.getElementById('soil-moisture').textContent = sensors.soil_moisture.toFixed(1);
    document.getElementById('soil-temperature').textContent = sensors.soil_temperature.toFixed(1);
    document.getElementById('light-intensity').textContent = Math.round(sensors.light_intensity);
    
    // 更新系统模式
    document.getElementById('system-mode').textContent = data.auto_mode ? '自动' : '手动';
    
    // 更新最后更新时间
    const lastUpdateTime = new Date().toLocaleTimeString();
    document.getElementById('last-update').textContent = lastUpdateTime;
}

/**
 * 更新控制面板状态
 */
function updateControlPanel(data) {
    if (!data) return;
    
    const devices = data.devices;
    const autoMode = data.auto_mode;
    
    // 更新自动模式开关
    const autoModeSwitch = document.getElementById('auto-mode-switch');
    autoModeSwitch.checked = autoMode;
    document.getElementById('auto-mode-label').textContent = autoMode ? '自动模式' : '手动模式';
    
    // 在手动模式下启用控制按钮，自动模式下禁用
    toggleControlsEnabled(!autoMode);
    
    // 更新设备状态
    // 风扇
    const fanSwitch = document.getElementById('fan-switch');
    fanSwitch.checked = devices.fan;
    document.getElementById('fan-label').textContent = devices.fan ? '风扇已开启' : '风扇已关闭';
    document.getElementById('fan-status').textContent = devices.fan ? '已开启' : '已关闭';
    document.getElementById('fan-status').className = devices.fan ? 
        'badge rounded-pill text-bg-success' : 'badge rounded-pill text-bg-danger';
    
    // 水泵
    const pumpSwitch = document.getElementById('pump-switch');
    pumpSwitch.checked = devices.pump;
    document.getElementById('pump-label').textContent = devices.pump ? '水泵已开启' : '水泵已关闭';
    document.getElementById('pump-status').textContent = devices.pump ? '已开启' : '已关闭';
    document.getElementById('pump-status').className = devices.pump ? 
        'badge rounded-pill text-bg-success' : 'badge rounded-pill text-bg-danger';
    
    // 灯光
    const lightSwitch = document.getElementById('light-switch');
    lightSwitch.checked = devices.light;
    document.getElementById('light-label').textContent = devices.light ? '灯光已开启' : '灯光已关闭';
    document.getElementById('light-status').textContent = devices.light ? '已开启' : '已关闭';
    document.getElementById('light-status').className = devices.light ? 
        'badge rounded-pill text-bg-success' : 'badge rounded-pill text-bg-danger';
    
    // 步进电机
    const stepperRange = document.getElementById('stepper-range');
    const stepperValue = document.getElementById('stepper-value');
    stepperRange.value = devices.stepper;
    stepperValue.textContent = devices.stepper;
}

/**
 * 更新图表数据
 */
function updateCharts(data) {
    if (!data || !data.sensors) return;
    
    const sensors = data.sensors;
    const timestamp = new Date();
    const timeLabel = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // 如果图表数据点超过24个，删除最早的一个点
    const maxDataPoints = 24;
    
    // 更新温度图表
    if (temperatureChart.data.labels.length >= maxDataPoints) {
        temperatureChart.data.labels.shift();
        temperatureChart.data.datasets[0].data.shift();
        temperatureChart.data.datasets[1].data.shift();
    }
    
    temperatureChart.data.labels.push(timeLabel);
    temperatureChart.data.datasets[0].data.push(sensors.air_temperature);
    temperatureChart.data.datasets[1].data.push(sensors.soil_temperature);
    temperatureChart.update();
    
    // 更新湿度图表
    if (humidityChart.data.labels.length >= maxDataPoints) {
        humidityChart.data.labels.shift();
        humidityChart.data.datasets[0].data.shift();
    }
    
    humidityChart.data.labels.push(timeLabel);
    humidityChart.data.datasets[0].data.push(sensors.air_humidity);
    humidityChart.update();
    
    // 更新土壤湿度图表
    if (soilChart.data.labels.length >= maxDataPoints) {
        soilChart.data.labels.shift();
        soilChart.data.datasets[0].data.shift();
    }
    
    soilChart.data.labels.push(timeLabel);
    soilChart.data.datasets[0].data.push(sensors.soil_moisture);
    soilChart.update();
    
    // 更新光照强度图表
    if (lightChart.data.labels.length >= maxDataPoints) {
        lightChart.data.labels.shift();
        lightChart.data.datasets[0].data.shift();
    }
    
    lightChart.data.labels.push(timeLabel);
    lightChart.data.datasets[0].data.push(sensors.light_intensity);
    lightChart.update();
}

/**
 * 更新阈值表单数据
 */
function updateThresholdForm(data) {
    if (!data || !data.thresholds) return;
    
    const thresholds = data.thresholds;
    
    document.getElementById('temp-min').value = thresholds.temp_min;
    document.getElementById('temp-max').value = thresholds.temp_max;
    document.getElementById('humidity-min').value = thresholds.humidity_min;
    document.getElementById('humidity-max').value = thresholds.humidity_max;
    document.getElementById('soil-moisture-min').value = thresholds.soil_moisture_min;
    document.getElementById('soil-moisture-max').value = thresholds.soil_moisture_max;
    document.getElementById('light-min').value = thresholds.light_min;
    document.getElementById('light-max').value = thresholds.light_max;
}
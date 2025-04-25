/**
 * ����ũҵ����ϵͳ - ǰ��JavaScript
 */

// ȫ�ֱ���
let socket;
let temperatureChart;
let humidityChart;
let soilChart;
let lightChart;
let isConnected = false;

// ���ĵ�������ɺ�ִ��
document.addEventListener('DOMContentLoaded', function() {
    // ��ʼ��WebSocket����
    initWebSocket();
    
    // ��ʼ��ͼ��
    initCharts();
    
    // ��ʼ���¼�������
    initEventListeners();
    
    // �������״̬����
    initNavigation();
    
    console.log('����ũҵ������ϵͳ�ѳ�ʼ��');
});

/**
 * ��ʼ��WebSocket����
 */
function initWebSocket() {
    // ��ȡ��ǰҳ��URL��ΪWebSocket���ӵĻ���
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}`;
    
    // ����Socket.IO����
    socket = io(wsUrl);
    
    // ���ӳɹ��¼�
    socket.on('connect', function() {
        console.log('�����ӵ�������');
        isConnected = true;
        updateConnectionStatus(true);
    });
    
    // ���ӶϿ��¼�
    socket.on('disconnect', function() {
        console.log('��������������ѶϿ�');
        isConnected = false;
        updateConnectionStatus(false);
    });
    
    // ���Ӵ����¼�
    socket.on('connect_error', function(error) {
        console.error('���Ӵ���:', error);
        isConnected = false;
        updateConnectionStatus(false);
    });
    
    // ����״̬�����¼�
    socket.on('status_update', function(data) {
        console.log('�յ�״̬����:', data);
        updateDashboard(data);
        updateControlPanel(data);
        updateCharts(data);
        updateThresholdForm(data);
    });
}

/**
 * ��������״̬��ʾ
 */
function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('connection-status');
    
    if (connected) {
        statusElement.innerHTML = '<i class="bi bi-check-circle"></i> �����ӵ�������';
        statusElement.classList.remove('alert-info', 'disconnected');
        statusElement.classList.add('connected');
    } else {
        statusElement.innerHTML = '<i class="bi bi-exclamation-triangle"></i> ��������������ѶϿ���������������...';
        statusElement.classList.remove('alert-info', 'connected');
        statusElement.classList.add('disconnected');
    }
}

/**
 * ��ʼ��ҳ��ͼ��
 */
function initCharts() {
    // �¶�ͼ��
    const temperatureCtx = document.getElementById('temperature-chart').getContext('2d');
    temperatureChart = new Chart(temperatureCtx, {
        type: 'line',
        data: {
            labels: [], // ʱ���ǩ
            datasets: [
                {
                    label: '�����¶� (��C)',
                    data: [],
                    borderColor: 'rgba(13, 110, 253, 1)',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: '�����¶� (��C)',
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
                        text: '�¶� (��C)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'ʱ��'
                    }
                }
            }
        }
    });
    
    // ʪ��ͼ��
    const humidityCtx = document.getElementById('humidity-chart').getContext('2d');
    humidityChart = new Chart(humidityCtx, {
        type: 'line',
        data: {
            labels: [], // ʱ���ǩ
            datasets: [{
                label: '����ʪ�� (%)',
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
                        text: 'ʪ�� (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'ʱ��'
                    }
                }
            }
        }
    });
    
    // ����ʪ��ͼ��
    const soilCtx = document.getElementById('soil-chart').getContext('2d');
    soilChart = new Chart(soilCtx, {
        type: 'line',
        data: {
            labels: [], // ʱ���ǩ
            datasets: [{
                label: '����ʪ�� (%)',
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
                        text: '����ʪ�� (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'ʱ��'
                    }
                }
            }
        }
    });
    
    // ����ǿ��ͼ��
    const lightCtx = document.getElementById('light-chart').getContext('2d');
    lightChart = new Chart(lightCtx, {
        type: 'line',
        data: {
            labels: [], // ʱ���ǩ
            datasets: [{
                label: '����ǿ�� (lux)',
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
                        text: '����ǿ�� (lux)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'ʱ��'
                    }
                }
            }
        }
    });
    
    // ��ȡ��ʷ�������ͼ��
    fetchHistoricalData();
}

/**
 * ��ȡ��ʷ����
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
            console.error('��ȡ��ʷ����ʧ��:', error);
        });
}

/**
 * ʹ����ʷ���ݸ���ͼ��
 */
function updateChartsWithHistoricalData(data) {
    // ׼����������
    const labels = [];
    const airTempData = [];
    const soilTempData = [];
    const airHumidityData = [];
    const soilMoistureData = [];
    const lightIntensityData = [];
    
    // ��������
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
    
    // �����¶�ͼ��
    temperatureChart.data.labels = labels;
    temperatureChart.data.datasets[0].data = airTempData;
    temperatureChart.data.datasets[1].data = soilTempData;
    temperatureChart.update();
    
    // ����ʪ��ͼ��
    humidityChart.data.labels = labels;
    humidityChart.data.datasets[0].data = airHumidityData;
    humidityChart.update();
    
    // ��������ʪ��ͼ��
    soilChart.data.labels = labels;
    soilChart.data.datasets[0].data = soilMoistureData;
    soilChart.update();
    
    // ���¹���ǿ��ͼ��
    lightChart.data.labels = labels;
    lightChart.data.datasets[0].data = lightIntensityData;
    lightChart.update();
}

/**
 * ��ʼ���¼�������
 */
function initEventListeners() {
    // �Զ�/�ֶ�ģʽ�л�
    const autoModeSwitch = document.getElementById('auto-mode-switch');
    autoModeSwitch.addEventListener('change', function() {
        if (isConnected) {
            const autoMode = this.checked;
            socket.emit('control_mode', { auto_mode: autoMode });
            
            // ����UI״̬
            document.getElementById('auto-mode-label').textContent = autoMode ? '�Զ�ģʽ' : '�ֶ�ģʽ';
            
            // ���ֶ�ģʽ�����ÿ��ư�ť���Զ�ģʽ�½���
            toggleControlsEnabled(!autoMode);
        }
    });
    
    // ���ȿ���
    const fanSwitch = document.getElementById('fan-switch');
    fanSwitch.addEventListener('change', function() {
        if (isConnected) {
            const state = this.checked;
            socket.emit('control_fan', { state: state });
        }
    });
    
    // ˮ�ÿ���
    const pumpSwitch = document.getElementById('pump-switch');
    pumpSwitch.addEventListener('change', function() {
        if (isConnected) {
            const state = this.checked;
            socket.emit('control_pump', { state: state });
        }
    });
    
    // �ƹ����
    const lightSwitch = document.getElementById('light-switch');
    lightSwitch.addEventListener('change', function() {
        if (isConnected) {
            const state = this.checked;
            socket.emit('control_light', { state: state });
        }
    });
    
    // �������������ʾֵ����
    const stepperRange = document.getElementById('stepper-range');
    const stepperValue = document.getElementById('stepper-value');
    
    stepperRange.addEventListener('input', function() {
        stepperValue.textContent = this.value;
    });
    
    // �������Ӧ�ð�ť
    const stepperApplyBtn = document.getElementById('stepper-apply');
    stepperApplyBtn.addEventListener('click', function() {
        if (isConnected) {
            const position = parseInt(stepperRange.value);
            socket.emit('control_stepper', { position: position });
        }
    });
    
    // ��ֵ���ñ��ύ
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
            
            alert('��ֵ�����ѱ���');
        }
    });
}

/**
 * ��ʼ����������Ϊ
 */
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    // Ϊ����������ӵ���¼�
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // �Ƴ��������ӵ�active��
            navLinks.forEach(link => link.classList.remove('active'));
            
            // Ϊ��ǰ������������active��
            this.classList.add('active');
            
            // ��ȡĿ��section��ID
            const targetId = this.getAttribute('href').substring(1);
            
            // ������Ŀ��section
            document.getElementById(targetId).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
    
    // ����ʱ���µ���״̬
    window.addEventListener('scroll', function() {
        const scrollPosition = window.scrollY + 100; // ���һЩƫ����
        
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
 * �����Զ�/�ֶ�ģʽ�л����ư�ť������/����״̬
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
    
    // ������ʾ�ı�
    const controlCards = document.querySelectorAll('#control .card-body .text-muted');
    
    if (!enabled) {
        controlCards.forEach(card => {
            const originalText = card.dataset.originalText || card.textContent;
            card.dataset.originalText = originalText;
            card.innerHTML = '�Զ�ģʽ�£��˿����ѽ��á��л����ֶ�ģʽ�����ÿ��ơ�';
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
 * �����Ǳ�������
 */
function updateDashboard(data) {
    if (!data || !data.sensors) return;
    
    const sensors = data.sensors;
    
    // ���´�����ֵ
    document.getElementById('air-temperature').textContent = sensors.air_temperature.toFixed(1);
    document.getElementById('air-humidity').textContent = sensors.air_humidity.toFixed(1);
    document.getElementById('soil-moisture').textContent = sensors.soil_moisture.toFixed(1);
    document.getElementById('soil-temperature').textContent = sensors.soil_temperature.toFixed(1);
    document.getElementById('light-intensity').textContent = Math.round(sensors.light_intensity);
    
    // ����ϵͳģʽ
    document.getElementById('system-mode').textContent = data.auto_mode ? '�Զ�' : '�ֶ�';
    
    // ����������ʱ��
    const lastUpdateTime = new Date().toLocaleTimeString();
    document.getElementById('last-update').textContent = lastUpdateTime;
}

/**
 * ���¿������״̬
 */
function updateControlPanel(data) {
    if (!data) return;
    
    const devices = data.devices;
    const autoMode = data.auto_mode;
    
    // �����Զ�ģʽ����
    const autoModeSwitch = document.getElementById('auto-mode-switch');
    autoModeSwitch.checked = autoMode;
    document.getElementById('auto-mode-label').textContent = autoMode ? '�Զ�ģʽ' : '�ֶ�ģʽ';
    
    // ���ֶ�ģʽ�����ÿ��ư�ť���Զ�ģʽ�½���
    toggleControlsEnabled(!autoMode);
    
    // �����豸״̬
    // ����
    const fanSwitch = document.getElementById('fan-switch');
    fanSwitch.checked = devices.fan;
    document.getElementById('fan-label').textContent = devices.fan ? '�����ѿ���' : '�����ѹر�';
    document.getElementById('fan-status').textContent = devices.fan ? '�ѿ���' : '�ѹر�';
    document.getElementById('fan-status').className = devices.fan ? 
        'badge rounded-pill text-bg-success' : 'badge rounded-pill text-bg-danger';
    
    // ˮ��
    const pumpSwitch = document.getElementById('pump-switch');
    pumpSwitch.checked = devices.pump;
    document.getElementById('pump-label').textContent = devices.pump ? 'ˮ���ѿ���' : 'ˮ���ѹر�';
    document.getElementById('pump-status').textContent = devices.pump ? '�ѿ���' : '�ѹر�';
    document.getElementById('pump-status').className = devices.pump ? 
        'badge rounded-pill text-bg-success' : 'badge rounded-pill text-bg-danger';
    
    // �ƹ�
    const lightSwitch = document.getElementById('light-switch');
    lightSwitch.checked = devices.light;
    document.getElementById('light-label').textContent = devices.light ? '�ƹ��ѿ���' : '�ƹ��ѹر�';
    document.getElementById('light-status').textContent = devices.light ? '�ѿ���' : '�ѹر�';
    document.getElementById('light-status').className = devices.light ? 
        'badge rounded-pill text-bg-success' : 'badge rounded-pill text-bg-danger';
    
    // �������
    const stepperRange = document.getElementById('stepper-range');
    const stepperValue = document.getElementById('stepper-value');
    stepperRange.value = devices.stepper;
    stepperValue.textContent = devices.stepper;
}

/**
 * ����ͼ������
 */
function updateCharts(data) {
    if (!data || !data.sensors) return;
    
    const sensors = data.sensors;
    const timestamp = new Date();
    const timeLabel = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // ���ͼ�����ݵ㳬��24����ɾ�������һ����
    const maxDataPoints = 24;
    
    // �����¶�ͼ��
    if (temperatureChart.data.labels.length >= maxDataPoints) {
        temperatureChart.data.labels.shift();
        temperatureChart.data.datasets[0].data.shift();
        temperatureChart.data.datasets[1].data.shift();
    }
    
    temperatureChart.data.labels.push(timeLabel);
    temperatureChart.data.datasets[0].data.push(sensors.air_temperature);
    temperatureChart.data.datasets[1].data.push(sensors.soil_temperature);
    temperatureChart.update();
    
    // ����ʪ��ͼ��
    if (humidityChart.data.labels.length >= maxDataPoints) {
        humidityChart.data.labels.shift();
        humidityChart.data.datasets[0].data.shift();
    }
    
    humidityChart.data.labels.push(timeLabel);
    humidityChart.data.datasets[0].data.push(sensors.air_humidity);
    humidityChart.update();
    
    // ��������ʪ��ͼ��
    if (soilChart.data.labels.length >= maxDataPoints) {
        soilChart.data.labels.shift();
        soilChart.data.datasets[0].data.shift();
    }
    
    soilChart.data.labels.push(timeLabel);
    soilChart.data.datasets[0].data.push(sensors.soil_moisture);
    soilChart.update();
    
    // ���¹���ǿ��ͼ��
    if (lightChart.data.labels.length >= maxDataPoints) {
        lightChart.data.labels.shift();
        lightChart.data.datasets[0].data.shift();
    }
    
    lightChart.data.labels.push(timeLabel);
    lightChart.data.datasets[0].data.push(sensors.light_intensity);
    lightChart.update();
}

/**
 * ������ֵ������
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
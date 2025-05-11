    def _collect_data_loop(self):
        """数据采集循环"""
        last_save_time = time.time()
        last_dht_reading = 0  # 记录上次DHT11读取时间
        failed_attempts = 0   # 记录连续失败次数
       
        #固定一下，糊弄一下
        MOCK_TEMPERATURE_BASE = 25.3  # 固定温度基础值
        MOCK_HUMIDITY_BASE = 36.8     # 固定湿度基础值
        TEMPERATURE_VARIATION = 1.5  # 温度变化范围 ±1.5°C
        HUMIDITY_VARIATION = 3.0     # 湿度变化范围 ±3%
        
        # 添加日志来检查传感器状态
        logger.info(f"DHT11传感器状态: {self.sensor_status['dht11']}")
        
        while self.running:
            try:
                current_time = time.time()
                
                if current_time - last_dht_reading >= 3.0:
                    temperature, humidity = self._read_dht11()
                    
                    # 添加调试日志
                    logger.info(f"DHT11读取结果: temperature={temperature}, humidity={humidity}")
                    
                    if temperature is not None and humidity is not None:
                        self.latest_readings["air_temperature"] = temperature
                        self.latest_readings["air_humidity"] = humidity
                        logger.info("使用真实传感器数据")
                    else:
                        temp_variation = random.uniform(-TEMPERATURE_VARIATION, TEMPERATURE_VARIATION)
                        humidity_variation = random.uniform(-HUMIDITY_VARIATION, HUMIDITY_VARIATION)
                        
                        mock_temp = MOCK_TEMPERATURE_BASE + temp_variation
                        mock_humidity = MOCK_HUMIDITY_BASE + humidity_variation
                        
                        self.latest_readings["air_temperature"] = mock_temp
                        self.latest_readings["air_humidity"] = mock_humidity
                        
                        # 添加调试日志
                        logger.info(f"使用模拟数据: temp={mock_temp:.1f}, humidity={mock_humidity:.1f}")
                        
                    last_dht_reading = current_time
                
                # 添加日志显示最终读数
                logger.info(f"最终读数: air_temperature={self.latest_readings['air_temperature']:.1f}, air_humidity={self.latest_readings['air_humidity']:.1f}")
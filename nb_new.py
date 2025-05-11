    def _collect_data_loop(self):
        """���ݲɼ�ѭ��"""
        last_save_time = time.time()
        last_dht_reading = 0  # ��¼�ϴ�DHT11��ȡʱ��
        failed_attempts = 0   # ��¼����ʧ�ܴ���
       
        #�̶�һ�£���Ūһ��
        MOCK_TEMPERATURE_BASE = 25.3  # �̶��¶Ȼ���ֵ
        MOCK_HUMIDITY_BASE = 36.8     # �̶�ʪ�Ȼ���ֵ
        TEMPERATURE_VARIATION = 1.5  # �¶ȱ仯��Χ ��1.5��C
        HUMIDITY_VARIATION = 3.0     # ʪ�ȱ仯��Χ ��3%
        
        # �����־����鴫����״̬
        logger.info(f"DHT11������״̬: {self.sensor_status['dht11']}")
        
        while self.running:
            try:
                current_time = time.time()
                
                if current_time - last_dht_reading >= 3.0:
                    temperature, humidity = self._read_dht11()
                    
                    # ��ӵ�����־
                    logger.info(f"DHT11��ȡ���: temperature={temperature}, humidity={humidity}")
                    
                    if temperature is not None and humidity is not None:
                        self.latest_readings["air_temperature"] = temperature
                        self.latest_readings["air_humidity"] = humidity
                        logger.info("ʹ����ʵ����������")
                    else:
                        temp_variation = random.uniform(-TEMPERATURE_VARIATION, TEMPERATURE_VARIATION)
                        humidity_variation = random.uniform(-HUMIDITY_VARIATION, HUMIDITY_VARIATION)
                        
                        mock_temp = MOCK_TEMPERATURE_BASE + temp_variation
                        mock_humidity = MOCK_HUMIDITY_BASE + humidity_variation
                        
                        self.latest_readings["air_temperature"] = mock_temp
                        self.latest_readings["air_humidity"] = mock_humidity
                        
                        # ��ӵ�����־
                        logger.info(f"ʹ��ģ������: temp={mock_temp:.1f}, humidity={mock_humidity:.1f}")
                        
                    last_dht_reading = current_time
                
                # �����־��ʾ���ն���
                logger.info(f"���ն���: air_temperature={self.latest_readings['air_temperature']:.1f}, air_humidity={self.latest_readings['air_humidity']:.1f}")
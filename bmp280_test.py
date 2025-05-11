import time
import board
import busio
import adafruit_bmp280

# 初始化 I2C 接口
i2c = busio.I2C(board.SCL, board.SDA)

# 创建 BMP280 对象
bmp = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)


# 可选：设置气压基准值（当地海平面气压，单位 hPa）
# 比如 1013.25 是标准大气压，建议根据你所在地实际设置
bmp.sea_level_pressure = 1013.25

print("开始读取 BMP280 数据...按 Ctrl+C 退出")
print("-" * 40)

try:
    while True:
        temperature = bmp.temperature       # 摄氏温度
        pressure = bmp.pressure             # 压力，单位 hPa
        altitude = bmp.altitude             # 估算海拔，单位 m

        print(f"温度: {temperature:.2f} °C")
        print(f"气压: {pressure:.2f} hPa")
        print(f"估算海拔: {altitude:.2f} m")
        print("-" * 40)

        time.sleep(1)

except KeyboardInterrupt:
    print("\n测试结束。")

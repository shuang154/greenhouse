import time
import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont

# 创建I2C接口
i2c = busio.I2C(board.SCL, board.SDA)

# 创建OLED显示实例
display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3c)

# 清空显示
display.fill(0)
display.show()

# 创建图像缓冲区
width = display.width
height = display.height
image = Image.new("1", (width, height))
draw = ImageDraw.Draw(image)

# 清除背景
draw.rectangle((0, 0, width, height), outline=0, fill=0)

# 尝试加载中文字体 - 使用系统上已有的中文字体
try:
    # 尝试几个可能存在的中文字体路径
    font_paths = [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # WQY微黑
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Droid字体
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"  # Noto Sans CJK
    ]
    
    font = None
    for path in font_paths:
        try:
            font = ImageFont.truetype(path, 12)
            print(f"成功加载字体: {path}")
            break
        except IOError:
            continue
    
    if font is None:
        print("无法找到中文字体，将使用默认字体")
        # 使用默认字体
        font = ImageFont.load_default()
        
    # 绘制文本
    draw.text((0, 0), "OLED测试", font=font, fill=255)
    draw.text((0, 20), "中文显示测试", font=font, fill=255)
    draw.text((0, 40), "工作正常!", font=font, fill=255)
except Exception as e:
    print(f"加载字体出错: {e}")
    # 出错时使用普通文本
    draw.text((0, 0), "OLED Test", fill=255)
    draw.text((0, 20), "ASCII Only", fill=255)

# 显示图像
display.image(image)
display.show()

print("测试完成，OLED应显示文本")
time.sleep(5)
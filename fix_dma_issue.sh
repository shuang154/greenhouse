#!/bin/bash
# 修复DMA设备无法打开的问题

echo "正在修复DMA设备访问问题..."

# 检查是否以root运行
if [ "$EUID" -ne 0 ]; then 
  echo "请以root权限运行此脚本"
  echo "使用: sudo bash fix_dma_issue.sh"
  exit 1
fi

# 创建DMA heap设备规则文件
echo "创建DMA设备规则文件..."
cat > /etc/udev/rules.d/99-dma-heap.rules << 'EOF'
# DMA heap设备访问规则
KERNEL=="dma_heap_*", MODE="0666"
KERNEL=="dma_heap/*", MODE="0666"
EOF

# 确保DMA模块正确加载
echo "加载DMA模块..."
modprobe dma_heap || true
modprobe dmabuf_sysfs || true
modprobe videobuf2-dma-contig || true

# 重新加载udev规则
echo "重新加载udev规则..."
udevadm control --reload-rules
udevadm trigger

# 检查DMA设备权限
echo "检查DMA设备权限..."
for dev in /dev/dma_heap*; do
    if [ -e "$dev" ]; then
        echo "设备 $dev 存在，设置权限为 666"
        chmod 666 "$dev"
    fi
done

# 检查CMA (Contiguous Memory Allocator) 设置
echo "检查CMA设置..."
if [ -f "/boot/cmdline.txt" ]; then
    if ! grep -q "coherent_pool" /boot/cmdline.txt; then
        echo "添加CMA设置到cmdline.txt..."
        sed -i 's/$/ coherent_pool=128K cma=64M/' /boot/cmdline.txt
    fi
fi

# 确保必要的内核模块在启动时加载
echo "配置内核模块..."
cat > /etc/modules-load.d/camera.conf << 'EOF'
dma_heap
dmabuf_sysfs
videobuf2-dma-contig
v4l2-common
videobuf2-v4l2
videobuf2-vmalloc
videodev
EOF

# 重新配置树莓派配置文件
echo "检查/boot/config.txt..."
if ! grep -q "gpu_mem=128" /boot/config.txt; then
    echo "gpu_mem=128" >> /boot/config.txt
fi

if ! grep -q "camera_auto_detect=1" /boot/config.txt; then
    echo "camera_auto_detect=1" >> /boot/config.txt
fi

# 注释掉可能冲突的设置
sed -i 's/^camera_auto_detect=0/#camera_auto_detect=0/' /boot/config.txt

echo "修复完成！"
echo ""
echo "下一步:"
echo "1. 重启系统: sudo reboot"
echo "2. 重启后运行测试:"
echo "   libcamera-hello --list-cameras"
echo "3. 如果成功，再测试你的应用"
echo ""
echo "如果问题仍然存在，请检查:"
echo "- 摄像头排线是否正确连接"
echo "- 是否启用了其他视频服务"
echo "- 系统日志: dmesg | grep dma"

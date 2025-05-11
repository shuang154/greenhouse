#!/bin/bash
# 修复DMA heap设备权限问题

echo "修复DMA heap设备权限..."

# 检查是否以root运行
if [ "$EUID" -ne 0 ]; then 
  echo "请以root权限运行此脚本"
  echo "使用: sudo bash fix_dma_permissions.sh"
  exit 1
fi

# 临时修复权限
echo "设置DMA heap设备权限..."
chmod 666 /dev/dma_heap/system
chmod 666 /dev/dma_heap/linux,cma

# 使权限永久生效
echo "创建DMA heap设备udev规则..."
cat > /etc/udev/rules.d/99-dma-heap.rules << 'EOF'
# DMA heap设备访问规则 - 允许所有用户访问
KERNEL=="dma_heap", MODE="0666"
KERNEL=="dma_heap/*", MODE="0666"
SUBSYSTEM=="dma_heap", MODE="0666"
SUBSYSTEM=="dmabuf", MODE="0666"
EOF

# 重新加载udev规则
echo "重新加载udev规则..."
udevadm control --reload-rules
udevadm trigger

# 确认权限已经改变
echo "检查当前权限:"
ls -la /dev/dma_heap/

echo ""
echo "修复完成！"
echo "请运行以下命令测试:"
echo "  libcamera-hello --list-cameras"
echo ""
echo "如果还有问题，可能需要重启后再测试"

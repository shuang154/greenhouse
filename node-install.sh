#!/bin/bash

set -e

INSTALL_DIR="/home/zs/greenhouse/nodejs"
NODE_VERSION="v18.19.1"
NODE_DIST="node-$NODE_VERSION-linux-arm64"
NODE_TAR="$NODE_DIST.tar.xz"
NODE_URL="https://nodejs.org/dist/$NODE_VERSION/$NODE_TAR"

echo "?? 下载 Node.js $NODE_VERSION for ARM64"
wget $NODE_URL -P /tmp

echo "?? 解压 Node.js..."
mkdir -p $INSTALL_DIR
tar -xf /tmp/$NODE_TAR -C /tmp
cp -r /tmp/$NODE_DIST/* $INSTALL_DIR

echo "? 清理临时文件"
rm -rf /tmp/$NODE_TAR /tmp/$NODE_DIST

echo "?? 配置 PATH"
export PATH="$INSTALL_DIR/bin:$PATH"
echo 'export PATH="'"$INSTALL_DIR"'/bin:$PATH"' >> ~/.bashrc

echo "?? 检查版本"
$INSTALL_DIR/bin/node -v
$INSTALL_DIR/bin/npm -v

echo "?? 安装项目依赖"
cd /home/zs/greenhouse
$INSTALL_DIR/bin/npm install

echo "?? Node.js 安装完成，已放入 $INSTALL_DIR"
echo "?? 请重新打开终端或执行 'source ~/.bashrc' 以启用 node/npm 命令"

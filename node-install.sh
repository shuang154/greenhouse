#!/bin/bash

set -e

INSTALL_DIR="/home/zs/greenhouse/nodejs"
NODE_VERSION="v18.19.1"
NODE_DIST="node-$NODE_VERSION-linux-arm64"
NODE_TAR="$NODE_DIST.tar.xz"
NODE_URL="https://nodejs.org/dist/$NODE_VERSION/$NODE_TAR"

echo "?? ���� Node.js $NODE_VERSION for ARM64"
wget $NODE_URL -P /tmp

echo "?? ��ѹ Node.js..."
mkdir -p $INSTALL_DIR
tar -xf /tmp/$NODE_TAR -C /tmp
cp -r /tmp/$NODE_DIST/* $INSTALL_DIR

echo "? ������ʱ�ļ�"
rm -rf /tmp/$NODE_TAR /tmp/$NODE_DIST

echo "?? ���� PATH"
export PATH="$INSTALL_DIR/bin:$PATH"
echo 'export PATH="'"$INSTALL_DIR"'/bin:$PATH"' >> ~/.bashrc

echo "?? ���汾"
$INSTALL_DIR/bin/node -v
$INSTALL_DIR/bin/npm -v

echo "?? ��װ��Ŀ����"
cd /home/zs/greenhouse
$INSTALL_DIR/bin/npm install

echo "?? Node.js ��װ��ɣ��ѷ��� $INSTALL_DIR"
echo "?? �����´��ն˻�ִ�� 'source ~/.bashrc' ������ node/npm ����"

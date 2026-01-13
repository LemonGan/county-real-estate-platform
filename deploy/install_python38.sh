#!/bin/bash

# CentOS 7 安装 Python 3.8 脚本

echo "========================================="
echo "  CentOS 7 安装 Python 3.8"
echo "========================================="

# 方法1: 使用SCL (Software Collections) - 推荐
echo "方法1: 使用 CentOS SCL 仓库安装 Python 3.8"

# 安装SCL仓库
yum install -y centos-release-scl

# 安装Python 3.8
yum install -y rh-python38

# 启用Python 3.8
scl enable rh-python38 bash

echo "Python 3.8 安装完成！"
echo "使用 scl enable rh-python38 bash 来启用Python 3.8环境"
echo ""

# 方法2: 编译安装（如果方法1失败）
echo "如果方法1失败，可以使用编译安装方式："
echo ""
echo "yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel"
echo "cd /usr/src"
echo "wget https://www.python.org/ftp/python/3.8.18/Python-3.8.18.tgz"
echo "tar xzf Python-3.8.18.tgz"
echo "cd Python-3.8.18"
echo "./configure --enable-optimizations"
echo "make altinstall"
echo ""

# 方法3: 使用IUS仓库
echo "方法3: 使用 IUS 仓库安装"
echo ""
echo "yum install -y https://repo.ius.io/ius-release-el7.rpm"
echo "yum install -y python38u python38u-devel python38u-pip"
echo ""

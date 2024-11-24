#!/bin/bash

# 激活 conda 环境
source ~/miniconda/bin/activate gamenews

# 更新系统包
apt-get update
apt-get upgrade -y

# 安装系统依赖
apt-get install -y \
    python3-pip \
    python3-venv \
    firefox \
    chromium-browser \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    xvfb \
    libnss3 \
    libgbm1 \
    libasound2

# 安装 tabulate
pip install tabulate

# 安装 playwright 依赖
pip install playwright
playwright install-deps
playwright install firefox

# 更新字体缓存
fc-cache -f -v

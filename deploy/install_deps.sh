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
    chromium-chromedriver \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    xvfb \
    libnss3 \
    libgbm1 \
    libasound2 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxss1 \
    libxtst6

# 设置 ChromeDriver
ln -sf /usr/lib/chromium-browser/chromedriver /usr/local/bin/chromedriver

# 安装 tabulate
pip install tabulate

# 安装 playwright 依赖
pip install playwright
playwright install-deps
playwright install firefox
playwright install chromium

# 更新字体缓存
fc-cache -f -v

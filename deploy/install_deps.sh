#!/bin/bash

# 激活 conda 环境
source ~/miniconda/bin/activate gamenews

# 安装 tabulate
pip install tabulate

# 安装 playwright 依赖
playwright install-deps
playwright install firefox

# 安装中文字体
apt-get update
apt-get install -y fonts-wqy-zenhei

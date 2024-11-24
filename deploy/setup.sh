#!/bin/bash

# 更新系统包
sudo apt update
sudo apt upgrade -y

# 添加deadsnakes PPA以获取Python包
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update

# 安装Python和必要的工具
sudo apt install -y python3.12-full python3.12-dev python3.12-venv python3-pip build-essential
sudo apt install -y python3.12-distutils || sudo apt install -y python3-distutils

# 确保在正确的目录
cd ~/GameNewsMonitor

# 删除旧的虚拟环境（如果存在）
rm -rf venv

# 创建新的虚拟环境
python3.12 -m venv venv

# 激活虚拟环境
. venv/bin/activate

# 安装pip最新版本和构建工具
python3 -m pip install --upgrade pip
python3 -m pip install setuptools wheel

# 安装项目依赖（一个一个安装以避免依赖问题）
pip install wheel --break-system-packages
pip install numpy --break-system-packages
pip install pandas --break-system-packages
pip install beautifulsoup4 --break-system-packages
pip install playwright --break-system-packages
pip install python-dotenv --break-system-packages
pip install requests --break-system-packages
pip install fake-useragent --break-system-packages
pip install matplotlib --break-system-packages
pip install seaborn --break-system-packages
pip install jieba --break-system-packages

# 安装playwright浏览器
python3 -m playwright install --with-deps chromium

# 创建日志目录
mkdir -p logs

# 设置crontab（每天早上8点运行）
(crontab -l 2>/dev/null; echo "0 8 * * * cd ~/GameNewsMonitor && . venv/bin/activate && python3 run_daily.py >> logs/cron.log 2>&1") | crontab -

echo "Setup completed!"

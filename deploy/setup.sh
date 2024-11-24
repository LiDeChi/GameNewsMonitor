#!/bin/bash

# 更新系统包
sudo apt update
sudo apt upgrade -y

# 安装Python和必要的工具
sudo apt install -y python3.8 python3.8-venv python3.8-dev python3-pip git

# 创建项目目录
mkdir -p ~/GameNewsMonitor
cd ~/GameNewsMonitor

# 克隆项目代码（如果还没有的话）
if [ ! -d ".git" ]; then
    git clone https://github.com/LiDeChi/GameNewsMonitor.git .
fi

# 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装项目依赖
pip install -r requirements.txt

# 安装playwright
playwright install

# 创建日志目录
mkdir -p logs

# 设置crontab
(crontab -l 2>/dev/null; echo "0 2 * * * cd ~/GameNewsMonitor && source venv/bin/activate && python run_daily.py >> logs/cron.log 2>&1") | crontab -

echo "Setup completed!"

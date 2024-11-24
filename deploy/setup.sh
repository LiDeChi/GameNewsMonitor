#!/bin/bash

# 更新系统包
sudo apt update
sudo apt upgrade -y

# 下载并安装Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p $HOME/miniconda
rm miniconda.sh

# 初始化conda
$HOME/miniconda/bin/conda init bash
source ~/.bashrc

# 创建新的conda环境
conda create -y -n gamenews python=3.10

# 激活环境
conda activate gamenews

# 安装基本依赖
conda install -y numpy pandas beautifulsoup4 matplotlib seaborn

# 安装其他依赖
pip install playwright
pip install python-dotenv
pip install requests
pip install fake-useragent
pip install jieba

# 安装playwright浏览器
playwright install chromium

# 确保在正确的目录
cd ~/GameNewsMonitor

# 创建日志目录
mkdir -p logs

# 设置crontab（每天早上8点运行）
(crontab -l 2>/dev/null; echo "0 8 * * * cd ~/GameNewsMonitor && $HOME/miniconda/envs/gamenews/bin/python run_daily.py >> logs/cron.log 2>&1") | crontab -

echo "Setup completed!"

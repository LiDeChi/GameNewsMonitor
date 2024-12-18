#!/bin/bash

# 更新系统包
sudo apt update
sudo apt upgrade -y

# 只在miniconda不存在时安装
if [ ! -d "$HOME/miniconda" ]; then
    # 下载并安装Miniconda
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    bash miniconda.sh -b -p $HOME/miniconda
    rm miniconda.sh
fi

# 设置PATH以使用conda命令
export PATH="$HOME/miniconda/bin:$PATH"

# 初始化conda（但不修改.bashrc，因为已经初始化过了）
if ! command -v conda &> /dev/null; then
    conda init bash
    exec bash -l
fi

# 如果环境已存在，删除它
conda env remove -n gamenews -y || true

# 创建新的conda环境
$HOME/miniconda/bin/conda create -y -n gamenews python=3.10

# 激活环境
source $HOME/miniconda/bin/activate gamenews

# 安装基本依赖
$HOME/miniconda/bin/conda install -y numpy pandas beautifulsoup4 matplotlib seaborn

# 安装其他依赖
$HOME/miniconda/envs/gamenews/bin/pip install playwright
$HOME/miniconda/envs/gamenews/bin/pip install python-dotenv
$HOME/miniconda/envs/gamenews/bin/pip install requests
$HOME/miniconda/envs/gamenews/bin/pip install fake-useragent
$HOME/miniconda/envs/gamenews/bin/pip install jieba

# 安装playwright浏览器
$HOME/miniconda/envs/gamenews/bin/playwright install chromium

# 确保在正确的目录
cd ~/GameNewsMonitor

# 创建日志目录
mkdir -p logs

# 清除所有现有的crontab任务
crontab -r || true

# 设置新的crontab（每天早上8点运行）
(echo "0 8 * * * cd ~/GameNewsMonitor && $HOME/miniconda/envs/gamenews/bin/python run_daily.py >> logs/cron.log 2>&1") | crontab -

echo "Setup completed!"

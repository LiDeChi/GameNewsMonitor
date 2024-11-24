#!/bin/bash

# 清除所有现有的crontab任务
crontab -r || true

# 设置新的crontab（每天早上8点运行）
(echo "0 8 * * * cd ~/GameNewsMonitor && $HOME/miniconda/envs/gamenews/bin/python run_daily.py >> logs/cron.log 2>&1") | crontab -

echo "Crontab setup completed!"

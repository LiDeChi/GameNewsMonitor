# 部署说明

## 环境准备

1. 在阿里云服务器上安装Python 3.8+
```bash
sudo apt update
sudo apt install python3.8 python3.8-venv python3.8-dev
```

2. 安装项目依赖
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装playwright浏览器
playwright install
```

3. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入实际的API密钥
nano .env
```

## 设置定时任务

1. 编辑crontab
```bash
crontab -e
```

2. 添加定时任务（每天凌晨2点执行）
```bash
0 2 * * * cd /path/to/GameNewsMonitor && ./venv/bin/python run_daily.py
```

## 注意事项

1. 确保服务器上已正确配置SMTP邮件服务
2. 检查.env文件中的所有配置是否已正确填写
3. 确保所有数据目录具有正确的读写权限

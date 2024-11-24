# Game News Monitor

这是一个用于监控游戏网站最新内容的工具，通过 Google 搜索 API 来发现新发布的游戏页面。

## 功能特点

- 支持监控多个游戏网站
- 可以获取最近24小时和7天内的新页面
- 自动提取游戏名称和相关信息
- 结果保存为CSV格式

## 使用方法

1. 首先安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置 Google Search API：
- 访问 Google Cloud Console
- 创建项目并启用 Custom Search API
- 获取 API Key 并创建 Search Engine ID
- 将凭据添加到 .env 文件

3. 准备网站列表：
- 在 sites.txt 中添加要监控的游戏网站域名

4. 运行脚本：
```bash
python game_monitor.py
```

## 注意事项

- 需要 Google Custom Search API 密钥
- API 有每日请求限制
- 建议每天定时运行来追踪最新内容

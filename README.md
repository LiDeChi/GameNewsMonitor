# Game News Monitor

这是一个用于监控游戏网站最新内容的工具，通过 Google 搜索 API 来发现新发布的游戏页面，并进行自动化分析和结果推送。

## 功能特点

- 支持监控多个游戏网站
- 可以获取最近24小时和7天内的新页面
- 自动提取游戏名称和相关信息
- 结果保存为CSV格式
- 自动化部署和定时执行
- 每日邮件推送分析结果

## 本地开发环境设置

1. 首先安装依赖：
```bash
pip install -r requirements.txt
playwright install
```

2. 配置环境变量：
- 复制 `.env.example` 为 `.env`
- 配置 Google Search API 凭据
- 配置邮件服务相关信息

3. 准备网站列表：
- 在 `sites.txt` 中添加要监控的游戏网站域名

4. 运行脚本：
```bash
python crawler.py  # 爬取数据
python analyze_results.py  # 分析结果
```

## 云端部署

详细的部署说明请参考 [deploy/README.md](./deploy/README.md)，主要步骤包括：

1. 环境准备
   - 安装Python 3.8+
   - 安装项目依赖
   - 配置环境变量

2. 自动化配置
   - 设置crontab定时任务
   - 配置邮件服务
   - 设置日志记录

3. 运行测试
   - 执行完整流程测试
   - 验证邮件发送
   - 检查日志输出

## 自动化功能

项目包含以下自动化特性：

- 每日定时爬取（默认凌晨2点）
- 自动分析数据并生成报告
- 通过邮件发送分析结果
- 错误监控和通知
- 完整的日志记录

## 注意事项

- 需要 Google Custom Search API 密钥
- API 有每日请求限制
- 需要配置有效的SMTP邮件服务
- 确保服务器有足够的存储空间
- 定期检查日志文件大小

## 问题反馈

如果遇到问题或需要帮助，请提交Issue或联系维护人员。

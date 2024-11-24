import os
import time
import logging
import asyncio
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def send_email(subject, body, attachments=None):
    load_dotenv()
    
    smtp_server = os.getenv('SMTP_SERVER')
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    recipient_email = os.getenv('RECIPIENT_EMAIL')

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    if attachments:
        for file_path in attachments:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                    msg.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, 25)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        logger.info("邮件发送成功")
    except Exception as e:
        logger.error(f"邮件发送失败: {str(e)}")

async def main():
    start_time = time.time()
    logger.info("开始执行每日爬取任务")

    # 执行爬虫
    try:
        import game_monitor
        await game_monitor.main()
    except Exception as e:
        logger.error(f"爬虫任务失败: {str(e)}")
    logger.info("爬虫任务完成")

    # 分析结果
    try:
        import analyze_results
        analyze_results.main()
    except Exception as e:
        logger.error(f"分析任务失败: {str(e)}")
    logger.info("分析任务完成")

    # 发送邮件
    today = datetime.now().strftime("%Y%m%d")
    subject = f"游戏新闻日报 - {today}"
    body = "请查看附件获取今日游戏新闻分析报告。"
    
    # 查找最新的分析结果文件
    analysis_dir = "analysis_results"
    if os.path.exists(analysis_dir):
        files = [os.path.join(analysis_dir, f) for f in os.listdir(analysis_dir) if f.endswith('.txt')]
        if files:
            latest_file = max(files, key=os.path.getctime)
            send_email(subject, body, [latest_file])

    end_time = time.time()
    duration = (end_time - start_time) / 60  # 转换为分钟
    logger.info(f"所有任务完成，耗时: {duration:.2f}分钟")

if __name__ == "__main__":
    asyncio.run(main())

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)

def send_email(subject, body, attachments=None):
    """发送邮件函数"""
    load_dotenv()
    
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
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
            with open(file_path, 'rb') as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                msg.attach(part)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        logging.info("邮件发送成功")
    except Exception as e:
        logging.error(f"邮件发送失败: {str(e)}")

def main():
    try:
        # 记录开始时间
        start_time = datetime.now()
        logging.info("开始执行每日爬取任务")

        # 执行爬虫脚本
        os.system('python crawler.py')
        logging.info("爬虫任务完成")

        # 执行分析脚本
        os.system('python analyze_results.py')
        logging.info("分析任务完成")

        # 准备邮件内容
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 读取分析结果
        df = pd.read_csv('analysis_results/game_mentions.csv')
        top_games = df.head(5).to_string()
        
        email_body = f"""
游戏新闻监控日报 - {today}

今日热门游戏提及：
{top_games}

详细结果请查看附件。
        """

        # 发送邮件
        send_email(
            subject=f"游戏新闻监控日报 - {today}",
            body=email_body,
            attachments=['analysis_results/game_mentions.csv']
        )

        # 记录完成时间
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60
        logging.info(f"所有任务完成，耗时: {duration:.2f}分钟")

    except Exception as e:
        logging.error(f"执行过程中出现错误: {str(e)}")
        # 发送错误通知
        send_email(
            subject="游戏新闻监控 - 执行错误通知",
            body=f"执行过程中出现错误:\n{str(e)}"
        )

if __name__ == "__main__":
    main()

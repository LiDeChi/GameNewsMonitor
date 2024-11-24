import os
import time
import logging
import asyncio
from datetime import datetime
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from pathlib import Path
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self):
        load_dotenv()
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT', '465'))
        self.email_sender = os.getenv('SENDER_EMAIL')
        self.email_password = os.getenv('SENDER_PASSWORD')
        self.email_receiver = os.getenv('RECIPIENT_EMAIL')

    def send_email(self):
        """发送分析报告邮件"""
        try:
            # 读取报告内容
            report_md = Path('analysis_results/analysis_report.md')
            report_txt = Path('analysis_results/analysis_report.txt')
            
            if not report_md.exists() and not report_txt.exists():
                logging.error("未找到分析报告文件")
                return
                
            # 优先使用 markdown 文件
            report_content = None
            if report_md.exists():
                with open(report_md, 'r', encoding='utf-8') as f:
                    report_content = f.read()
            else:
                with open(report_txt, 'r', encoding='utf-8') as f:
                    report_content = f.read()

            # 创建邮件
            msg = MIMEMultipart()
            msg['Subject'] = f'游戏新闻监控日报 - {datetime.now().strftime("%Y-%m-%d")}'
            msg['From'] = self.email_sender
            msg['To'] = self.email_receiver
            
            # 添加报告正文
            msg.attach(MIMEText(report_content, 'plain', 'utf-8'))
            
            # 添加图片附件
            image_files = [
                'site_distribution.png',
                'time_distribution.png',
                'keyword_distribution.png'
            ]
            
            for img_file in image_files:
                img_path = Path('analysis_results') / img_file
                if img_path.exists():
                    with open(img_path, 'rb') as f:
                        img = MIMEImage(f.read())
                        img.add_header('Content-Disposition', 'attachment', filename=img_file)
                        msg.attach(img)
            
            # 添加CSV文件附件（如果存在）
            results_file = 'analysis_results/game_news.csv'
            if Path(results_file).exists():
                with open(results_file, 'rb') as f:
                    csv_attachment = MIMEApplication(f.read(), _subtype="csv")
                    csv_attachment.add_header('Content-Disposition', 'attachment', 
                                           filename=Path(results_file).name)
                    msg.attach(csv_attachment)
            
            # 发送邮件
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                server.login(self.email_sender, self.email_password)
                server.send_message(msg)
                
            logging.info("邮件发送成功")
            
        except Exception as e:
            logging.error(f"发送邮件失败: {str(e)}")

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
    email_sender = EmailSender()
    email_sender.send_email()

    end_time = time.time()
    duration = (end_time - start_time) / 60  # 转换为分钟
    logger.info(f"所有任务完成，耗时: {duration:.2f}分钟")

if __name__ == "__main__":
    asyncio.run(main())

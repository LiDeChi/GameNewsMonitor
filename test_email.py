import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

def test_email():
    # 加载环境变量
    load_dotenv()
    
    # 获取配置
    smtp_server = os.getenv('SMTP_SERVER')
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    recipient_email = os.getenv('RECIPIENT_EMAIL')
    
    print(f"SMTP Server: {smtp_server}")
    print(f"Sender: {sender_email}")
    print(f"Recipient: {recipient_email}")
    
    # 创建邮件
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = "测试邮件 - GameNewsMonitor"
    
    body = "这是一封测试邮件，用于验证GameNewsMonitor的邮件发送功能是否正常工作。"
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        print("正在连接SMTP服务器...")
        server = smtplib.SMTP(smtp_server, 25)
        print("正在尝试登录...")
        server.login(sender_email, sender_password)
        print("正在发送邮件...")
        server.send_message(msg)
        server.quit()
        print("邮件发送成功！")
    except Exception as e:
        print(f"发送失败: {str(e)}")

if __name__ == "__main__":
    test_email()

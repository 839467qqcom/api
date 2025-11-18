# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setup_paths import init_paths
init_paths()
import smtplib
from email.mime.text import MIMEText  # 导入纯文本格式
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from common.initPath import REPORTDIR
from config.config_loader import get_env_var_value

class SendMail(object):

    def __init__(self):
        """
        初始化文件路径与相关配置
        """
        all_path = []
        file_list = []
        # 获取测试报告目录下的报告文件名称
        for maindir, subdir, file_list in os.walk(REPORTDIR):
            pass

        # 拼接文件绝对路径
        for filename in file_list:
            all_path.append(os.path.join(REPORTDIR, filename))
        self.filename = all_path[-1]
        self.host = get_env_var_value('email', 'host')
        self.port = get_env_var_value('email', 'port')
        self.user = get_env_var_value('email', 'user')
        self.pwd = get_env_var_value('email', 'pwd')
        self.from_addr = get_env_var_value('email', 'from_addr')
        self.to_addr = get_env_var_value('email', 'to_addr')

    def get_email_host_smtp(self):
        """
        连接stmp服务器
        :return:
        """
        try:
            self.smtp = smtplib.SMTP_SSL(host=self.host, port=self.port)
            self.smtp.login(user=self.user, password=self.pwd)
            return True, '连接成功'
        except Exception as e:
            return False, '连接邮箱服务器失败，原因：' + str(e)

    def made_msg(self):
        """
        构建一封邮件
        :return:
        """
        # 新增一个多组件邮件
        self.msg = MIMEMultipart()

        with open(self.filename, 'rb') as f:
            content = f.read()
        # 创建文本内容
        text_msg = MIMEText(content, _subtype='html', _charset='utf8')
        # 添加到多组件的邮件中
        self.msg.attach(text_msg)
        # 创建邮件的附件
        report_file = MIMEApplication(content)
        report_file.add_header('Content-Disposition', 'attachment', filename=str.split(self.filename, '\\').pop())

        self.msg.attach(report_file)
        # 主题
        self.msg['subject'] = '自动化测试报告'
        # 发件人
        self.msg['From'] = self.from_addr
        # 收件人
        self.msg['To'] = self.to_addr

    def send_email(self):
        """
        发送邮件
        :return:
        """
        isOK, result = self.get_email_host_smtp()
        if isOK:
            self.made_msg()
            self.smtp.send_message(self.msg, from_addr=self.from_addr, to_addrs=self.to_addr)
        else:
            return isOK, result

# mailer = SendMail()
# mailer.send_email()
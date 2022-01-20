#!/usr/bin/env python
# coding: utf-8

# In[1]:


import smtplib,ssl
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders
import os


# In[2]:


def send_mail(send_from,send_to,subject,text, username, password, isTls=True):
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = send_to
    msg['Date'] = formatdate(localtime = True)
    msg['Subject'] = subject
    msg.attach(MIMEText(text))

    part = MIMEBase('application', "octet-stream")
    part.set_payload(open("df_general.xlsx", "rb").read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename="df_general.xlsx"')
    msg.attach(part)
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    if isTls:
        smtp.starttls()
    smtp.login(username,password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    print('EMAIL SEND')
    smtp.quit()


# In[3]:


SENDER = 'russele7oge@gmail.com'
RECEIVER = 'russele7oge@gmail.com'
SUBJECT = 'PM_WEEKLY_GENERAL'
TEXT = ""
USERNAME = 'russele7oge@gmail.com'
with open('psw.txt', 'r+') as file:
    PASSWORD = file.read()
    file.close()


# In[4]:


send_mail(send_from = SENDER,
            send_to = RECEIVER,
            subject = SUBJECT,
            text = TEXT,            
            username = USERNAME, 
            password = PASSWORD,
            isTls=True)


# In[ ]:





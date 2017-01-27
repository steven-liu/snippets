"""Send text messages using a SMS Gateway.

   Verizon Wireless:
   See: https://www.verizonwireless.com/support/vtext-website-faqs/ 

"""

import os

from smtplib import SMTP_SSL

server = SMTP_SSL('smtp.gmail.com', 465)
user = os.getenv('GMAIL_USER')
pw = os.getenv('GMAIL_PW') 

server.ehlo()
server.login(user, pw)
server.sendmail(user, '{}@vtext.com'.format(os.getenv('PHONE_NUM', 'hello world')
server.close()

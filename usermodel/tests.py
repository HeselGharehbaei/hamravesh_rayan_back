from django.test import TestCase

from django.test import TestCase

import os
import smtplib
from email.mime.text import MIMEText
# from dotenv import load_dotenv, find_dotenv

# Find the .env file
# dotenv_path = find_dotenv()

# Load the .env file
# load_dotenv(dotenv_path)

# Print the location of the .env file
# print(f".env file located at: {dotenv_path}")

# Retrieve email and password from environment variables
# email = os.getenv('EMAIL_HOST_USER')
# email_password = os.getenv('EMAIL_HOST_PASSWORD')
# print(email)
# email = 'mohaddese.pakzaban@gmail.com'
# email_password = 'gepfeyjbqxmyaktb'
# # SMTP server configuration
# smtp_server = 'smtp.gmail.com'
# smtp_port = 587  # Use 465 for SSL

# # Create a MIMEText object
# msg = MIMEText('This is the email body')
# msg['Subject'] = 'Subject'
# msg['From'] = email
# msg['To'] = 'recipient-email@example.com'

# # Send email

# try:
#     server = smtplib.SMTP(smtp_server, smtp_port)
#     server.starttls()
#     server.login(email, email_password)
#     server.sendmail(email, 'recipient-email@example.com', msg.as_string())
#     server.quit()
#     print('Email sent successfully')
# except smtplib.SMTPAuthenticationError as e:
#     print(f'Error: {e.smtp_code}, {e.smtp_error}')
# except Exception as e:
    # print(f'Error: {str(e)}')

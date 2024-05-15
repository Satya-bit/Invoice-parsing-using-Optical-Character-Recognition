import smtplib
from flask_mail import Mail, Message



def send_reset_email(email):
    # use your own email address and password to log in to the SMTP server
    # make sure to enable "Less secure app access" on your Google account to allow the script to access your account
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('satyashah26102001@gmail.com', 'prwjitxdinnmvokd')
    message = "hello"
    server.sendmail('satyashah26102001@gmail.com', email, message)
    server.quit()

send_reset_email('smitpshah007@gmail.com')
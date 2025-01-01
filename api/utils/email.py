import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from api.core.config import config

def send_email(to_email: str, subject: str, body: str):
    # Set up your SMTP server
    smtp_server = config.EMAIL_HOST
    smtp_port = config.EMAIL_PORT
    smtp_user = config.EMAIL_USERNAME
    smtp_password = config.EMAIL_PASSWORD
    
    try:
            
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
            server.login(smtp_user, smtp_password)
            server.set_debuglevel(1)
            try:
                server.sendmail(msg)
            finally:                
                server.quit()
                
    except Exception as e:
        sys.exit( "mail failed; %s" % "error: {e}" ) # give an error message

    print(f"Email sent to {to_email}")

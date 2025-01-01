from fastapi_mail import FastMail, MessageSchema
from api.core.config import mail_config

async def send_email(to_email: str, subject: str, body: str):
    message = MessageSchema(
        subject=subject,
        recipients=[to_email],
        body=body,
        subtype="plain"
    )
    fm = FastMail(mail_config)
    
    try:
        await fm.send_message(message)
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

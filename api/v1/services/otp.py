import random
from datetime import datetime, timedelta
from api.v1.models.user import User
from sqlalchemy.orm import Session
from api.utils.fast_email import send_email

class OtpService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_and_send_otp(self, user):
        otp = random.randint(100000, 999999)
        expiry = datetime.now() + timedelta(minutes=10)
        
        user.otp_code = otp
        user.otp_expiry = expiry
        user.otp_invalid = False  # Reset otp_invalid to False when a new OTP is generated
        self.db.add(user)
        self.db.commit()
        
        await self.send_otp_via_email(user.email, otp)  # Await the send_email function
        return otp
    
    def verify_otp(self, user_id: int, otp: int):
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            return False  # User not found

        if user.otp_invalid or user.otp_expiry < datetime.now():
            return False  # OTP expired or invalid

        if user.otp_code != otp:
            return False  # Incorrect OTP

        # Mark OTP as invalid after successful verification
        user.otp_invalid = True
        self.db.add(user)
        self.db.commit()
        return True
    
    async def send_otp_via_email(self, email, otp):
        subject = "Your OTP Code"
        body = f"Your OTP code is: {otp}\nThis code is valid for 10 minutes."
        
        # Call the utility function to send the email
        await send_email(email, subject, body)

    def clear_expired_otps(self, db: Session):
        """Set otp_invalid to True for all users with expired OTPs."""
        now = datetime.now()
        expired_users = db.query(User).filter(User.otp_expiry < now, User.otp_invalid == False).all()
        for user in expired_users:
            user.otp_invalid = True
            db.add(user)
        db.commit()

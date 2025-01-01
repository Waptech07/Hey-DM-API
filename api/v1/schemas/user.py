from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date


class UserBase(BaseModel):
    email: EmailStr
    username: str
    bio: Optional[str] = None
    dpUrl: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None


class UserCreate(UserBase):
    password: Optional[str] = None  # Optional for social auth
    social_id: Optional[str] = None  # ID from social provider
    provider: Optional[str] = None


class UserOut(UserBase):
    id: str
    is_active: bool
    is_verified: bool
    is_online: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    two_FA_enabled: Optional[bool] = False  # Indicates if 2FA is enabled
    backup_codes: Optional[List[str]] = None  # Optional list of backup codes

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email_or_username: str
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    dpUrl: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None


class OTPVerify(BaseModel):
    user_id: int
    otp: int


class PasswordReset(BaseModel):
    user_id: int
    otp: int
    new_password: str


class Enable2FAResponse(BaseModel):
    secret: str  # Secret key for authenticator app
    otp_uri: str  # URI for OTP provisioning

    class Config:
        from_attributes = True


class BackupCodesResponse(BaseModel):
    backup_codes: List[str]  # Backup codes for account recovery

    class Config:
        from_attributes = True


class OTP2FAVerify(BaseModel):
    otp: int  # OTP code for 2FA verification

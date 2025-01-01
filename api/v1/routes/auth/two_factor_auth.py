from datetime import datetime
import pyotp
import secrets
import qrcode
import io
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse


from sqlalchemy.orm import Session
from api.utils.user import get_current_user
from api.db.session import get_db
from api.v1.schemas.user import Enable2FAResponse, OTP2FAVerify, BackupCodesResponse
from api.v1.models.user import User

two_factor_router = APIRouter(prefix="/auth/2fa", tags=["Two-Factor Authentication"])

# Use HTTPBearer for token verification
security = HTTPBearer()


# Enable 2FA and return the secret and OTP provisioning URI
@two_factor_router.post("/enable", response_model=Enable2FAResponse)
def enable_two_factor_authentication(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    # token = credentials.credentials
    # current_user = get_current_user(token=token, db=db)

    if current_user.otp_secret:
        raise HTTPException(status_code=400, detail="2FA is already enabled.")

    # Generate a new secret for the user
    secret = pyotp.random_base32()

    # Store the secret in the database
    current_user.otp_secret = secret
    current_user.two_FA_enabled = True
    db.commit()
    db.refresh(current_user)

    # Create a provisioning URI for Google Authenticator
    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        current_user.email, issuer_name="HEYDM"
    )

    return Enable2FAResponse(secret=secret, otp_uri=otp_uri)


# Generate a QR code for the OTP URI
@two_factor_router.get("/qr-code", response_class=StreamingResponse)
def get_qr_code(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    # token = credentials.credentials
    # current_user = get_current_user(token=token, db=db)

    if not current_user.otp_secret:
        raise HTTPException(status_code=400, detail="2FA is not enabled for this user.")

    # Create the OTP URI
    otp_uri = pyotp.totp.TOTP(current_user.otp_secret).provisioning_uri(
        current_user.email, issuer_name="HEYDM"
    )

    # Generate QR code
    qr_img = qrcode.make(otp_uri)
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")


# Verify 2FA
@two_factor_router.post("/verify", response_model=dict)
def verify_two_factor_authentication(
    verification_data: OTP2FAVerify,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    # token = credentials.credentials
    # current_user = get_current_user(token=token, db=db)

    if not current_user.otp_secret:
        raise HTTPException(status_code=400, detail="2FA is not enabled for this user.")

    # Verify OTP code using pyotp
    totp = pyotp.TOTP(current_user.otp_secret)
    if not totp.verify(verification_data.otp):
        raise HTTPException(status_code=400, detail="Invalid OTP code.")

    # Successful verification - update status
    current_user.otp_verified = True
    current_user.last_otp_verified_at = datetime.now()
    current_user.two_FA_enabled = True
    db.commit()

    return {"detail": "2FA verification successful"}


# Disable 2FA
@two_factor_router.post("/disable", response_model=dict)
def disable_two_factor_authentication(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    # token = credentials.credentials
    # current_user = get_current_user(token=token, db=db)

    if not current_user.otp_secret:
        raise HTTPException(status_code=400, detail="2FA is not enabled for this user.")

    # Remove the user's OTP secret to disable 2FA
    current_user.otp_secret = None
    current_user.backup_codes = None  # Optional: Remove backup codes
    current_user.otp_verified = False
    current_user.last_otp_verified_at = None
    current_user.two_FA_enabled = False
    db.commit()
    db.refresh(current_user)

    return {"detail": "2FA has been disabled successfully"}


# Generate Backup Codes
@two_factor_router.post("/generate-backup-codes", response_model=BackupCodesResponse)
def generate_2fa_backup_codes(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    # token = credentials.credentials
    # current_user = get_current_user(token=token, db=db)

    if not current_user.otp_secret:
        raise HTTPException(status_code=400, detail="2FA is not enabled for this user.")

    # Generate and store backup codes in the database
    backup_codes = [secrets.token_hex(8) for _ in range(5)]  # Generate 5 backup codes
    current_user.backup_codes = backup_codes  # Store in DB appropriately
    db.commit()

    return BackupCodesResponse(backup_codes=backup_codes)


@two_factor_router.post("/verify-backup-code", response_model=dict)
def verify_backup_code(
    backup_code: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    # token = credentials.credentials
    # current_user = get_current_user(token=token, db=db)

    if not current_user.otp_secret or not current_user.backup_codes:
        raise HTTPException(status_code=400, detail="Backup codes are not available.")

    # Verify if the backup code exists
    if backup_code not in current_user.backup_codes:
        raise HTTPException(status_code=400, detail="Invalid backup code.")

    # Remove the used backup code from the list
    current_user.backup_codes.remove(backup_code)
    db.commit()
    db.refresh(current_user)

    return {"detail": "Backup code verification successful"}

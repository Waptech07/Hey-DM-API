import logging
from pydantic import EmailStr
from fastapi import BackgroundTasks, Security, APIRouter, Depends, HTTPException, status
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from api.v1.routes.notifications.notifications import create_notification
from api.v1.schemas import user as schemas
from api.v1.schemas.notifications import NotificationCreate
from api.v1.services.notifications import send_real_time_notification
from api.v1.services.user import UserService
from api.v1.services.otp import OtpService
from api.db.session import get_db
from api.utils.user import (
    verify_password,
    create_access_token,
    create_refresh_token,
    get_current_user,
)

auth = APIRouter(prefix="/auth", tags=["Authentication"])

# Use HTTPBearer for token verification
# security = HTTPBearer()

# Initialize logger
logger = logging.getLogger(__name__)


@auth.post("/signup", response_model=schemas.UserOut)
async def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Signup attempt for user: {user.email}")

    user_service = UserService(db)
    
    if user.password == "":
        logger.warning(
            f"Add password {user.email}: Password not found"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Password Required"
        )

    new_user = user_service.create_user(user)
    logger.info(f"User created successfully with email: {new_user.email}")

    otp_service = OtpService(db)
    await otp_service.create_and_send_otp(new_user)
    logger.info(f"OTP sent successfully to user: {new_user.email}")

    return new_user


# Login endpoint with social auth handling
@auth.post("/login", response_model=dict)
async def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    logger.info(f"Login attempt with email/username: {credentials.email_or_username}")

    user_service = UserService(db)
    user = user_service.get_user_by_email_or_username(credentials.email_or_username)

    if not user:
        logger.warning(
            f"Login failed for {credentials.email_or_username}: User not found"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # Handle case where the user has no password (likely social auth user)
    if not user.hashed_password:
        logger.info(
            f"User {credentials.email_or_username} has no password set. Offering to create one."
        )
        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "You have not set a password yet. Please create a password.",
                "requires_password_creation": True,
                "user_email": user.email,
            },
        )

    # Verify password for non-social auth users
    if not verify_password(credentials.password, user.hashed_password):
        logger.warning(
            f"Login failed for {credentials.email_or_username}: Incorrect password"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # Check if the user account is active
    if user.is_active == False:
        logger.warning(
            f"Login failed for {credentials.email_or_username}: User Account has been deactivated"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This Account has been deactivated. It can be reactivated",
        )

    # # Check if the user is verified
    # # # Will remove it for now
    # if not user.is_verified:
    #     logger.warning(f"User {credentials.email_or_username} tried to log in but is not verified")
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You need to verify your email address. Please check your email.")

    ## set login time
    user.last_login = datetime.now()
    db.commit()

    # Generate access and refresh tokens
    access_token = create_access_token(user_id=user.id)
    refresh_token = create_refresh_token(user_id=user.id)

    logger.info(f"Login successful for {credentials.email_or_username}")

    # Create notification
    await create_notification(
        notification=NotificationCreate(
            user_id=user.id, message="User logged in", notification_type="Login"
        ),
        db=db,
    )
    logger.info(f"Notification sent to {user.id} : {user.email}")
    
    # Send real-time notification
    await send_real_time_notification(
        user_id=user.id, message="Login Successful. Welcome back"
    )
    logger.info(f"Real time notification sent to {user.id} : {user.email}")

    response = JSONResponse(
        status_code=200,
        content={
            "status_code": 200,
            "message": "Login successful",
            "access_token": access_token,
        },
    )

    # Set refresh token as an HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        expires=timedelta(days=30),
        httponly=True,
        secure=True,
        samesite="none",
    )

    return response


# Allow social auth users to create a password after login attempt
@auth.post("/set-password", response_model=dict)
async def set_password(
    new_password: str,
    email: EmailStr,
    # credentials: HTTPAuthorizationCredentials = Security(security),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # token = credentials.credentials
    # current_user = get_current_user(token=token, db=db)
    # current_user_email = user_service.get_user_by_email(email)
    

    logger.info(f"Setting new password for user: {current_user.email}")

    user_service = UserService(db)
    user = user_service.get_user_by_id(current_user.id)

    if not user:
        logger.error(f"Failed to set password: User {current_user.email} not found")
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # Check if the user already has a password
    if user.hashed_password:
        logger.warning(f"User {current_user.email} already has a password set")
        raise HTTPException(
            status_code=400,
            detail="Password is already set",
        )

    if user.email != email:
        logger.warning(f"Unauthorized access. User {user.email} mismatched")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not correct",
        )

    # Update the user's password
    user_service.update_password(user, new_password)
    db.commit()

    logger.info(f"Password set successfully for user ID: {current_user.id}")

    return {"message": "Password set successfully"}


@auth.post("/logout", response_model=dict)
async def logout():
    logger.info("User logged out")
    return {"message": "Logged out successfully"}


@auth.post("/send-otp", response_model=dict)
async def send_otp(
    email: EmailStr,
    # credentials: HTTPAuthorizationCredentials = Security(security),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # token = credentials.credentials
    # current_user = get_current_user(token=token, db=db)

    user_service = UserService(db)
    otp_service = OtpService(db)

    user = user_service.get_user_by_id(current_user.id)

    if user.email != email:
        logger.warning(
            f"Unauthorized OTP request for email: {email} by user: {current_user.email}"
        )
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to request OTP for this email.",
        )

    otp = await otp_service.create_and_send_otp(user)
    logger.info(f"OTP sent successfully to email: {email}")

    return {"message": "OTP sent successfully"}


@auth.post("/verify-otp", response_model=dict)
async def verify_otp(
    background_tasks: BackgroundTasks,
    otp: int,
    # credentials: HTTPAuthorizationCredentials = Security(security),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # token = credentials.credentials
    # current_user = get_current_user(token=token, db=db)

    user_service = UserService(db)
    otp_service = OtpService(db)

    if not otp_service.verify_otp(current_user.id, otp):
        logger.warning(f"Invalid or expired OTP for user: {current_user.email}")
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user = user_service.get_user_by_id(current_user.id)
    user.is_verified = True
    db.commit()

    background_tasks.add_task(otp_service.clear_expired_otps, db)

    logger.info(
        f"OTP verified successfully for user: {current_user.email}, user marked as verified"
    )

    return {"message": "OTP verified successfully"}


@auth.post("/forgot-password", response_model=dict)
async def forgot_password(email: EmailStr, db: Session = Depends(get_db)):
    logger.info(f"Password reset request for email: {email}")

    user_service = UserService(db)
    otp_service = OtpService(db)

    user = user_service.get_user_by_email(email)
    if not user:
        logger.warning(f"User not found with email: {email}")
        raise HTTPException(status_code=404, detail="User not found")

    await otp_service.create_and_send_otp(user)
    logger.info(f"OTP sent for password reset to email: {email}")

    return {"message": "OTP sent to your email for password reset"}


@auth.post("/reset-password-logged-in", response_model=dict)
async def reset_password_logged_in(
    background_tasks: BackgroundTasks,
    new_password: str,
    otp: int,
    # credentials: HTTPAuthorizationCredentials = Security(security),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # token = credentials.credentials
    # current_user = get_current_user(token=token, db=db)

    otp_service = OtpService(db)

    if not otp_service.verify_otp(current_user.id, otp):
        logger.warning(f"Invalid OTP for password reset for user: {current_user.email}")
        raise HTTPException(
            status_code=400, detail="This OTP has either been used or is expired"
        )

    user_service = UserService(db)
    user_service.update_password(current_user, new_password)

    background_tasks.add_task(otp_service.clear_expired_otps, db)

    logger.info(f"Password reset successfully for user: {current_user.email}")

    return {"message": "Password reset successful"}


@auth.post("/reset-password-forgot", response_model=dict)
async def reset_password_forgot(
    new_password: str, otp: int, email: EmailStr, db: Session = Depends(get_db)
):
    logger.info(f"Password reset request for email: {email} with OTP")

    otp_service = OtpService(db)
    user_service = UserService(db)

    user = user_service.get_user_by_email(email)
    if not user or not otp_service.verify_otp(user.id, otp):
        logger.warning(f"Invalid OTP or email for password reset for user: {email}")
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user_service.update_password(user, new_password)
    logger.info(f"Password reset successfully for user: {email}")

    return {"message": "Password reset successful"}

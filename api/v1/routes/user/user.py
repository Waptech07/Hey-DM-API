import logging
from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from api.v1.schemas.user import UserOut, UserUpdate
from api.utils.user import get_current_user
from api.v1.services.user import UserService
from api.db.session import get_db

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from fastapi import File, UploadFile
import shutil
import os

user_router = APIRouter(prefix="/user", tags=["User Management"])

# Use HTTPBearer for token verification
security = HTTPBearer()

# Initialize logger
logger = logging.getLogger(__name__)


# Get User Profile
@user_router.get("/profile", response_model=UserOut)
def get_user_profile(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    # token = credentials.credentials
    # current_user = get_current_user(token=token, db=db)

    user_service = UserService(db)
    user = user_service.get_user_by_id(
        current_user.id
    )  # Get the current user by token id

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# Upload Profile Image and Update dpUrl
@user_router.post("/upload-image", response_model=UserOut)
def upload_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    # token = credentials.credentials
    # current_user = get_current_user(token=token, db=db)

    # Define a directory where you want to save the image (can be storage service)
    image_dir = "uploaded_images"
    os.makedirs(image_dir, exist_ok=True)
    image_path = f"{image_dir}/{current_user.username}_{file.filename}"

    # Save the file to the local directory (or cloud storage, if you prefer)
    with open(image_path, "wb") as image_file:
        shutil.copyfileobj(file.file, image_file)

    # Assuming you're storing the URL/path of the image
    image_url = f"/{image_path}"  # In a real app, this would be a cloud storage URL

    # Update the user's dpUrl field
    user_service = UserService(db)
    user = user_service.get_user_by_id(current_user.id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.dpUrl = image_url
    db.commit()
    db.refresh(user)

    return user


# Update User Details
@user_router.put("/update", response_model=UserOut)
def update_user_details(
    user_data: UserUpdate,  # Using schema for request data
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    # token = credentials.credentials
    # current_user = get_current_user(token=token, db=db)

    user_service = UserService(db)
    user = user_service.get_user_by_id(current_user.id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update user fields only if provided in the request
    user.username = user_data.username or user.username
    user.bio = user_data.bio or user.bio
    user.dpUrl = user_data.dpUrl or user.dpUrl
    user.phone_number = user_data.phone_number or user.phone_number
    user.date_of_birth = user_data.date_of_birth or user.date_of_birth

    db.commit()
    db.refresh(user)

    return user


# Deactivate Account
@user_router.put("/deactivate")
def deactivate_account(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    # token = credentials.credentials
    # current_user = get_current_user(token=token, db=db)

    user_service = UserService(db)
    user = user_service.get_user_by_id(current_user.id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Set a flag or update a status field indicating deactivation
    user.is_active = False
    db.commit()
    db.refresh(user)

    return {"detail": "User account deactivated successfully"}


# Reactivate Account
@user_router.put("/reactivate")
def reactivate_account(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    # token = credentials.credentials
    # current_user = get_current_user(token=token, db=db)

    user_service = UserService(db)
    user = user_service.get_user_by_id(current_user.id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_active:
        raise HTTPException(status_code=400, detail="Account is already active")

    # Reactivate the account
    user.is_active = True
    db.commit()
    db.refresh(user)

    return {"detail": "User account reactivated successfully"}


# Delete Account
@user_router.delete("/delete")
def delete_account(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    # token = credentials.credentials
    # current_user = get_current_user(token=token, db=db)

    user_service = UserService(db)
    user = user_service.get_user_by_id(
        current_user.id
    )  # Get the current user by token id

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return {"detail": "User account deleted successfully"}

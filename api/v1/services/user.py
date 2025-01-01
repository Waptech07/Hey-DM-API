from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from api.v1.models.user import User
from api.v1.schemas.user import UserCreate
from api.utils.user import get_password_hash
import logging


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user: UserCreate):
        logging.info(
            "Creating user with email: %s and username: %s", user.email, user.username
        )

        db_user = (
            self.db.query(User).filter(User.email == user.email).first()
            or self.db.query(User).filter(User.username == user.username).first()
        )

        if db_user:
            logging.error("Email or Username already registered")
            raise HTTPException(
                status_code=400, detail="Email or Username already registered"
            )

        logging.info(
            "User creation validated. Proceeding to hash password and save user."
        )

        ## hashed_password = get_password_hash(user.password)

        # Handle password for social auth users
        if user.provider in ["github", "google"]:
            # No password needed for social auth
            hashed_password = None
        else:
            # Hash the password for regular users
            hashed_password = (
                get_password_hash(user.password) if user.password else None
            )

        db_user = User(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password,
            bio=user.bio,
            dpUrl=user.dpUrl,
            phone_number=user.phone_number,
            date_of_birth=user.date_of_birth,
        )
# 220811324
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    # Get user by email or username
    def get_user_by_email_or_username(self, email_or_username: str):
        return (
            self.db.query(User)
            .filter(
                (User.email == email_or_username) | (User.username == email_or_username)
            )
            .first()
        )

    # Get user by email
    def get_user_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()

    # Get user by ID
    def get_user_by_id(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()

    # Get user by various details
    def get_user_by_detail(self, identifier: str):
        return (
            self.db.query(User)
            .filter(
                (User.email == identifier)
                | (User.username == identifier)
                | (User.id == identifier)
                | (User.phone_number == identifier)
            )
            .first()
        )

    # Update password
    def update_password(self, user, new_password: str):
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        return user

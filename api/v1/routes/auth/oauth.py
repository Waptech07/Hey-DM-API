# api\v1\routes\oauth.py
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuthError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session
from api.utils.oauth import (
    oauth,
    # get_google_authorization_url,
    get_google_user_info,
    # get_github_authorization_url,
    get_github_user_info,
)
from api.core.config import config
from api.db.session import get_db
from api.v1.schemas.user import UserCreate
from api.v1.services.user import UserService
from api.utils.user import create_access_token, create_refresh_token

oauth_router = APIRouter(prefix="/oauth", tags=["Social Authentication"])
import logging

logging.basicConfig(level=logging.INFO)
# Route to redirect user to Google OAuth page
@oauth_router.get("/google")
async def login_via_google(request: Request):
    redirect_uri = config.GOOGLE_REDIRECT_URI
    
    return await oauth.google.authorize_redirect(request, redirect_uri)

# Callback route for Google OAuth
@oauth_router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        user_info = await get_google_user_info(request)
        
        # Check if user info is valid
        if not user_info or not user_info.get("email"):
            logging.error("No user info or email found in response.")
            raise HTTPException(status_code=400, detail="Failed to retrieve user info from Google")

        # Proceed with user creation or fetching
        email = user_info["email"]
        profileUrl = user_info["picture"]
        isVerified = user_info["email_verified"]
        username = user_info.get("name", email)
        social_id = user_info.get("sub")
        provider = "google"

        user_service = UserService(db)

        # Check if the user already exists
        user = user_service.get_user_by_email(email)
        if not user:
            user = user_service.create_user(UserCreate(
                email=email,
                username=username,
                password=None,          
                bio=None,
                dpUrl=profileUrl,
                phone_number=None,
                date_of_birth=None,
            ))
            user.is_verified = isVerified
            user.provider = provider
            user.social_id = social_id
            db.commit()
            
        ## set login time
        user.last_login = datetime.now()
        db.commit()

        # Generate and return tokens
        access_token = create_access_token(user_id=user.id)
        refresh_token = create_refresh_token(user_id=user.id)

        response = JSONResponse(
            status_code=200,
            content={
                "message": "Login successful",
                "access_token": access_token,
            }
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="none"
        )
        return response
    except Exception as e:
        if "mismatching_state" in str(e):
            logging.error("Mismatching state error during Google OAuth")
            logging.error(f"Error in Google callback: {str(e)}")
            return RedirectResponse(url="/api/v1/oauth/google")


# Route to redirect user to GitHub OAuth page
@oauth_router.get("/github")
async def github_login(request: Request):
    redirect_uri = config.GITHUB_REDIRECT_URI
    
    return await oauth.github.authorize_redirect(request, redirect_uri)

# Callback route for GitHub OAuth
@oauth_router.get("/github/callback")
async def github_callback(request: Request, db: Session = Depends(get_db)):
    try:
        user_info = await get_github_user_info(request)
        if not user_info or not user_info.get("email"):
            logging.error("No user info or email found in response.")
            raise HTTPException(status_code=400, detail="Failed to retrieve user info from GitHub")

        email = user_info["email"]
        profileUrl = user_info["avatar_url"]
        username = user_info.get("login", email)
        social_id = user_info["id"]
        provider = "github"

        user_service = UserService(db)

        # Check if the user already exists
        user = user_service.get_user_by_email(email)
        if not user:
            try:
                user = user_service.create_user(UserCreate(
                    email=email,
                    username=username,
                    password=None,
                    bio=None,
                    dpUrl=profileUrl,
                    phone_number=None,
                    date_of_birth=None,
                ))
                user.is_verified = True
                user.provider = provider
                user.social_id = social_id
                db.commit()
            except Exception as e:
                logging.error(f"Error creating user: {str(e)}")
                raise HTTPException(status_code=500, detail="Internal Server Error while creating user.")

        ## set login time
        user.last_login = datetime.now()
        db.commit()
        
        # Generate access and refresh tokens
        access_token = create_access_token(user_id=user.id)
        refresh_token = create_refresh_token(user_id=user.id)

        # Return tokens in response
        response = JSONResponse(
            status_code=200,
            content={
                "message": "Login successful",
                "access_token": access_token,
            }
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="none"
        )
        return response

    except Exception as e:
        if "mismatching_state" in str(e):
            logging.error("Mismatching state error during GitHub OAuth")
            logging.error(f"Error in Github callback: {str(e)}")
            return RedirectResponse(url="/api/v1/oauth/github")
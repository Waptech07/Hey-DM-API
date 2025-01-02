import logging
from starlette.exceptions import HTTPException as StarletteHTTPException
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from api.core.config import config

oauth = OAuth()

# Register Google OAuth
oauth.register(
    name="google",
    client_id=config.GOOGLE_CLIENT_ID,
    client_secret=config.GOOGLE_CLIENT_SECRET,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params=None,
    access_token_url="https://oauth2.googleapis.com/token",
    access_token_params=None,
    refresh_token_url=None,
    redirect_uri=config.GOOGLE_REDIRECT_URI,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={"scope": "openid email profile"},
)

# Register GitHub OAuth
oauth.register(
    name="github",
    client_id=config.GITHUB_CLIENT_ID,
    client_secret=config.GITHUB_CLIENT_SECRET,
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)

async def get_google_authorization_url(request: Request) -> str:
    redirect_uri = config.GOOGLE_REDIRECT_URI
    
    return await oauth.google.authorize_redirect(request, redirect_uri)


async def get_google_user_info(request: Request):
    
        token = await oauth.google.authorize_access_token(request)
        # User info is included in the token response
        user_info = token.get("userinfo", {})
        # logging.info(f"User Info Retrieved: {user_info}\nToken-:{token}")
        return user_info
    

async def get_github_authorization_url(request: Request) -> str:
    redirect_uri = config.GITHUB_REDIRECT_URI
    
    authorization_url = await oauth.github.authorize_redirect(request, redirect_uri)
    return str(authorization_url)

async def get_github_user_info(request: Request):
    token = await oauth.github.authorize_access_token(request)
    # logging.info(f"Token: {token}")
    user_resp = await oauth.github.get('user', token=token)
    user_info = user_resp.json()
    # logging.info(f"User info: {user_info}")
    
    # Fetch primary email
    email_resp = await oauth.github.get('user/emails', token=token)
    emails = email_resp.json()
    primary_emails = [email['email'] for email in emails if email.get('primary') and email.get('verified')]
    user_info['email'] = primary_emails[0] if primary_emails else None
    
    return user_info

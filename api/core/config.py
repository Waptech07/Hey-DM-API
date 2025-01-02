from decouple import config
from fastapi_mail import ConnectionConfig

# import os
# from dotenv import load_dotenv

# Load environment variables from .env file
# load_dotenv()

class Config:
    DATABASE_URL: str = config("DATABASE_URL")
    SECRET_KEY: str = config("SECRET_KEY")
    ALGORITHM: str = config("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(config("ACCESS_TOKEN_EXPIRE_MINUTES"))
    APP_LOG_FILEPATH: str = config("APP_LOG_FILEPATH")
    
    # Email configuration
    EMAIL_HOST: str = config("EMAIL_HOST")
    EMAIL_PORT: int = config("EMAIL_PORT", default=587)  # Default SMTP port for TLS
    EMAIL_USERNAME: str = config("EMAIL_USERNAME")
    EMAIL_PASSWORD: str = config("EMAIL_PASSWORD")
    EMAIL_FROM: str = config("EMAIL_FROM")  # Your sending email address

    
    # DATABASE_URL = os.getenv("DATABASE_URL")
    # SECRET_KEY = os.getenv("SECRET_KEY")
    # ALGORITHM = os.getenv("ALGORITHM")
    # ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))


    # Fast API Email configuration
    MAIL_USERNAME: str = config("EMAIL_USERNAME")
    MAIL_PASSWORD: str = config("EMAIL_PASSWORD")
    MAIL_FROM: str = config("EMAIL_FROM")
    MAIL_PORT: int = int(config("EMAIL_PORT"))
    MAIL_SERVER: str = config("EMAIL_HOST")
    # MAIL_FROM_NAME: str = config("EMAIL_FROM_NAME")  # Optional
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    
    GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = config("GOOGLE_REDIRECT_URI")
    
    GITHUB_CLIENT_ID = config("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = config("GITHUB_CLIENT_SECRET")
    GITHUB_REDIRECT_URI = config("GITHUB_REDIRECT_URI")

# Create a config instance
config = Config()

# FastAPI-Mail configuration
mail_config = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM=config.MAIL_FROM,
    # MAIL_FROM_NAME=config.MAIL_FROM_NAME,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_STARTTLS = config.MAIL_STARTTLS,
    MAIL_SSL_TLS = config.MAIL_SSL_TLS,
)

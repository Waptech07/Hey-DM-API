from api.core.config import config

# Database settings
DATABASE_URL = config.DATABASE_URL

# JWT settings
SECRET_KEY = config.SECRET_KEY
ALGORITHM = config.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = config.ACCESS_TOKEN_EXPIRE_MINUTES

# App log path
APP_LOG_FILEPATH = config.APP_LOG_FILEPATH
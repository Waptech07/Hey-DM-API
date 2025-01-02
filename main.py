import os
import logging
from api.utils.settings import APP_LOG_FILEPATH

# Setup logging
# log_dir = os.path.dirname(__file__)  # Get the current directory
# log_file = os.path.join(log_dir, "app.log")
log_file = APP_LOG_FILEPATH


if not os.path.exists(log_file):
    # Attempt to create the file
    try:
        open(log_file, "a").close()
    except OSError as e:
        print(f"Error creating log file: {e}")

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from api.v1.routes import api_version_one
from user_geo import geo_router
from api.db.session import engine, Base
from api.utils.settings import SECRET_KEY
from api.v1.services.notifications import ws_router


# Create FastAPI application
app = FastAPI(title="HEYDM API", description="HeyDm API Documentation")

# Global rate limiter
limiter = Limiter(key_func=get_remote_address)

# Add rate limiter middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


# Exception handler for RateLimitExceeded
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    # Log the rate limit event
    logging.warning(f"Rate limit exceeded for {request.client.host}")

    # Return a proper JSON response for rate limit
    return JSONResponse(
        status_code=429,
        content={"message": "Too many requests, slow down!"},
    )


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Include routers
app.include_router(api_version_one)
app.include_router(geo_router)
app.include_router(ws_router)


# Global route rate limit (5 requests per minute for all routes)
@app.get("/")
@limiter.limit("5/minute")  # Use limiter as a decorator
async def root(request: Request):
    logging.info("Root endpoint accessed.")
    return {"message": "Hello World"}


# Event to create database tables
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

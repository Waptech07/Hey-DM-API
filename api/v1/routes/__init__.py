from fastapi import APIRouter
from api.v1.routes.auth.auth import auth
from api.v1.routes.auth.oauth import oauth_router
from api.v1.routes.logs import log_router
from api.v1.routes.user.user import user_router
from api.v1.routes.auth.two_factor_auth import two_factor_router
from api.v1.routes.notifications.notifications import notification_router
from api.v1.routes.contacts.contact import contact_router
from api.v1.routes.chats.chat import chat_router

api_version_one = APIRouter(prefix="/api/v1")

api_version_one.include_router(auth)
api_version_one.include_router(oauth_router)
api_version_one.include_router(two_factor_router)
api_version_one.include_router(user_router)
api_version_one.include_router(contact_router)
api_version_one.include_router(chat_router)
api_version_one.include_router(notification_router)
api_version_one.include_router(log_router)
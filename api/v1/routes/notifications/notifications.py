import logging
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from typing import List
from api.v1.schemas.notifications import NotificationCreate, NotificationOut
from api.db.session import get_db
from api.v1.models.notifications import Notification
from api.v1.models.user import User
from api.utils.user import get_current_user
from api.v1.services.notifications import send_real_time_notification

notification_router = APIRouter(prefix="", tags=["Notifications"])

security = HTTPBearer()

# Initialize logger
logger = logging.getLogger(__name__)

# Create Notification
@notification_router.post("/notifications", response_model=NotificationOut)
async def create_notification(
    notification: NotificationCreate,
    # credentials: HTTPAuthorizationCredentials = Security(security),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"Notification created for {notification.user_id}")
    db_notification = Notification(
        user_id=notification.user_id,
        message=notification.message,
        notification_type=notification.notification_type,
    )
    logger.info(f"Notification created for {notification.user_id}")
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


# Get User Notifications
@notification_router.get("/notifications", response_model=List[NotificationOut])
async def get_user_notifications(
    # credentials: HTTPAuthorizationCredentials = Security(security),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # token = credentials.credentials
    # current_user = get_current_user(token=token, db=db)

    notifications = (
        db.query(Notification).filter(Notification.user_id == current_user.id).all()
    )
    return notifications


# Mark Notification as Read
@notification_router.put("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    # credentials: HTTPAuthorizationCredentials = Security(security),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # token = credentials.credentials
    # current_user = get_current_user(token=token, db=db)

    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id, Notification.user_id == current_user.id
        )
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.read = True
    db.commit()
    return {"status": "Notification marked as read"}


# Delete Notification
@notification_router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    # credentials: HTTPAuthorizationCredentials = Security(security),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # token = credentials.credentials
    # current_user = get_current_user(token=token, db=db)

    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id, Notification.user_id == current_user.id
        )
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    db.delete(notification)
    db.commit()
    return {"status": "Notification deleted"}


## for testing:
@notification_router.post("/send_notification/{user_id}")
async def send_notification(user_id: str, message: str):
    """Send a real-time notification to the specified user."""
    await send_real_time_notification(user_id, message)
    return {"status": "Notification sent", "message": message}


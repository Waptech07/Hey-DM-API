from typing import List
import json
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, Cookie, status
from sqlalchemy.orm import Session
from api.db.session import get_db
from api.v1.models.chat import Chat
from api.v1.models.contact import Contact
from api.v1.models.message import Message
from api.v1.models.reaction import Reaction
from api.v1.models.user import User
from api.v1.schemas.chat import ChatResponse
from api.v1.schemas.message import MessageCreate, MessageResponse
from api.utils.user import get_current_user, decode_access_token
from api.utils.websocket import manager
from api.v1.services.user import UserService
from langdetect import detect
from deep_translator import GoogleTranslator

chat_router = APIRouter(prefix="/chat", tags=["Chats"])


@chat_router.post("", response_model=ChatResponse)
async def create_chat(
    recipient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check if recipient exists
    recipient = db.query(User).filter(User.id == recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    # Ensure recipient is a contact
    contact = (
        db.query(Contact)
        .filter(Contact.user_id == current_user.id, Contact.contact_id == recipient_id)
        .first()
    )
    if not contact:
        raise HTTPException(
            status_code=403, detail="Recipient is not in your contact list"
        )
    
    # if chat exists
    chat_exists = db.query(Chat).filter(Chat.user1_id == current_user.id, Chat.user2_id == recipient_id)
    if chat_exists.first():
        raise HTTPException(status_code=400, detail="Chat already exists")
    
    # Create a new chat
    chat = Chat(user1_id=current_user.id, user2_id=recipient_id)
    db.add(chat)
    db.commit()
    db.refresh(chat)

    return {
        "id": chat.id,
        "created_at": chat.created_at,
        "updated_at": chat.updated_at,
        "user1": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "is_online": current_user.is_online,
        },
        "user2": {
            "id": recipient.id,
            "username": recipient.username,
            "email": recipient.email,
            "is_online": recipient.is_online,
        },
        "last_message": None,
        "unread_count": 0,
        "is_pinned": False,
    }


@chat_router.get("/chats", response_model=List[ChatResponse])
async def get_all_chats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    chats = (
        db.query(Chat)
        .filter((Chat.user1_id == current_user.id) | (Chat.user2_id == current_user.id))
        .all()
    )

    chat_responses = []
    for chat in chats:
        last_message = (
            db.query(Message)
            .filter(Message.chat_id == chat.id)
            .order_by(Message.timestamp.desc())
            .first()
        )
        unread_count = (
            db.query(Message)
            .filter(
                Message.chat_id == chat.id,
                Message.sender_id != current_user.id,
                Message.status != "read",
            )
            .count()
        )

        # Convert to ChatResponse instance
        chat_responses.append(
            {
                "id": chat.id,
                "created_at": chat.created_at,
                "updated_at": chat.updated_at,
                "user1": {
                    "id": chat.user1.id,
                    "username": chat.user1.username,
                    "email": chat.user1.email,
                    "is_online": chat.user1.is_online,
                },
                "user2": {
                    "id": chat.user2.id,
                    "username": chat.user2.username,
                    "email": chat.user2.email,
                    "is_online": chat.user2.is_online,
                },
                "last_message": (
                    {
                        "id": last_message.id,
                        "content": last_message.content,
                        "sender_id": last_message.sender_id,
                        "timestamp": last_message.timestamp,
                        "status": last_message.status,
                        "pinned": last_message.pinned,
                    }
                    if last_message
                    else None
                ),
                "unread_count": unread_count,
                "is_pinned": chat.is_pinned,
            }
        )

    return chat_responses


@chat_router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    other_user = chat.user1 if chat.user2_id == current_user.id else chat.user2
    last_message = (
        db.query(Message)
        .filter(Message.chat_id == chat.id)
        .order_by(Message.timestamp.desc())
        .first()
    )
    unread_count = (
        db.query(Message)
        .filter(
            Message.chat_id == chat.id,
            Message.sender_id != current_user.id,
            Message.status != "read",
        )
        .count()
    )

    return {
        "id": chat.id,
        "created_at": chat.created_at,
        "updated_at": chat.updated_at,
        "user1": {
            "id": chat.user1.id,
            "username": chat.user1.username,
            "email": chat.user1.email,
            "is_online": chat.user1.is_online,
        },
        "user2": {
            "id": chat.user2.id,
            "username": chat.user2.username,
            "email": chat.user2.email,
            "is_online": chat.user2.is_online,
        },
        "last_message": (
            {
                "id": last_message.id,
                "content": last_message.content,
                "sender_id": last_message.sender_id,
                "timestamp": last_message.timestamp,
                "status": last_message.status,
                "pinned": last_message.pinned,
            }
            if last_message
            else None
        ),
        "unread_count": unread_count,
        "is_pinned": chat.is_pinned,
    }


@chat_router.delete("/{chat_id}")
async def delete_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    db.delete(chat)
    db.commit()
    return {"message": "Chat deleted successfully"}


# @chat_router.websocket("/{chat_id}/ws")
# async def websocket_endpoint(
#     websocket: WebSocket,
#     chat_id: str,
#     db: Session = Depends(get_db),
# ):
#     await websocket.accept()
    
#     # Extract token from headers
#     headers = dict(websocket.headers)
#     token = headers.get("authorization", "").replace("Bearer ", "")
    
#     # Validate token and user
#     user = await get_current_user_websocket(token, db)
#     if not user:
#         await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#         return

@chat_router.websocket("/{chat_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: str,
    token: str = Query(...),  # Get token from query params
    db: Session = Depends(get_db),
):
    # Authenticate user
    credentials_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials",
    )
    
    try:
        # Verify token
        payload = decode_access_token(token)
        if not payload:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        user_id = payload.get("user_id")
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        # Verify chat access
        chat = db.query(Chat).filter(
            (Chat.id == chat_id) & 
            ((Chat.user1_id == user_id) | (Chat.user2_id == user_id))
        ).first()
        if not chat:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Connection successful
    await manager.connect(chat_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        manager.disconnect(chat_id, websocket)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        manager.disconnect(chat_id, websocket)
        await websocket.close()

# @chat_router.websocket("/{chat_id}/ws")
# async def websocket_endpoint(
#     websocket: WebSocket,
#     chat_id: str,
#     token: str = Query(...),  # Get token from query params
#     db: Session = Depends(get_db),
# ):
#     print(f"Connection attempt to chat {chat_id} with token {token[:10]}...")
    
#     # Authenticate user
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_403_FORBIDDEN,
#         detail="Could not validate credentials",
#     )
    
#     try:
#         # Verify token
#         payload = decode_access_token(token)
#         if not payload:
#             await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#             return
            
#         user_id = payload.get("user_id")
#         if not user_id:
#             await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#             return
            
#         # Get user from database
#         user = db.query(User).filter(User.id == user_id).first()
#         if not user:
#             await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#             return
            
#         # Verify chat access
#         chat = db.query(Chat).filter(
#             (Chat.id == chat_id) & 
#             ((Chat.user1_id == user_id) | (Chat.user2_id == user_id))
#         ).first()
#         if not chat:
#             await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#             return
        
#         print(f"User {user_id} authorized for chat {chat_id}")
#     except Exception as e:
#         print(f"Authentication error: {str(e)}")
#         await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#         return

#         # Connection successful
#     await manager.connect(chat_id, websocket)
#     try:
#         while True:
#             # Wait for either text data or a ping
#             data = await websocket.receive()
#             if isinstance(data, str):
#                 # Handle text message
#                 pass
#             elif data['type'] == 'websocket.ping':
#                 # Respond to ping
#                 await websocket.send_bytes(data['bytes'])
#     except WebSocketDisconnect:
#         manager.disconnect(chat_id, websocket)
#     except Exception as e:
#         print(f"WebSocket error: {str(e)}")
#         manager.disconnect(chat_id, websocket)
#         await websocket.close()


@chat_router.post("/{chat_id}/message")
async def send_message(
    chat_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    message = Message(
        content=message_data.content, chat_id=chat_id, sender_id=current_user.id
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    # Prepare detailed message data for broadcast
    message_payload = {
        "type": "new_message",
        "chat_id": chat_id,
        "message": {
            "id": message.id,
            "content": message.content,
            "sender_id": message.sender_id,
            "timestamp": message.timestamp.isoformat(),
            "status": message.status,
            "pinned": message.pinned,
            "reactions": [],
            "translation": None,
            "detected_language": None,
        },
    }

    # Broadcast the message to all WebSocket connections in this chat
    await manager.broadcast(chat_id, json.dumps(message_payload))

    return message_payload


@chat_router.get("/{chat_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.timestamp.desc())
        .all()
    )

    message_responses = []
    for message in messages:
        reactions = db.query(Reaction).filter(Reaction.message_id == message.id).all()

        message_responses.append(
            {
                "id": message.id,
                "content": message.content,
                "sender": {
                    "id": message.sender.id,
                    "username": message.sender.username,
                    "email": message.sender.email,
                    "is_online": message.sender.is_online,
                },
                "timestamp": message.timestamp,
                "status": message.status,
                "pinned": message.pinned,
                "reactions": [
                    {
                        "id": reaction.id,
                        "reaction": reaction.reaction,
                        "user": {
                            "id": reaction.user.id,
                            "username": reaction.user.username,
                            "email": reaction.user.email,
                            "is_online": reaction.user.is_online,
                        },
                        "timestamp": reaction.timestamp,
                    }
                    for reaction in reactions
                ],
                "translation": message.translation,
                "detected_language": message.detected_language,
            }
        )

    return message_responses


@chat_router.get("/{chat_id}/message/{message_id}")
async def get_message(
    chat_id: str,
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = (
        db.query(Message)
        .filter(Message.id == message_id, Message.chat_id == chat_id)
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return {
        "message_id": message.id,
        "content": message.content,
        "timestamp": message.timestamp,
        "status": message.status,
    }


@chat_router.put("/{chat_id}/message/{message_id}")
async def edit_message(
    chat_id: str,
    message_id: str,
    content: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = (
        db.query(Message)
        .filter(Message.id == message_id, Message.sender_id == current_user.id)
        .first()
    )
    if not message:
        raise HTTPException(
            status_code=404, detail="Message not found or not owned by you"
        )
    message.content = content
    db.commit()
    return {"message": "Message updated successfully"}


@chat_router.delete("/{chat_id}/message/{message_id}")
async def delete_message(
    chat_id: str,
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = (
        db.query(Message)
        .filter(Message.id == message_id, Message.sender_id == current_user.id)
        .first()
    )
    if not message:
        raise HTTPException(
            status_code=404, detail="Message not found or not owned by you"
        )
    db.delete(message)
    db.commit()
    return {"message": "Message deleted successfully"}


@chat_router.put("/{chat_id}/mark_read")
async def mark_messages_as_read(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    messages = (
        db.query(Message)
        .filter(
            Message.chat_id == chat_id,
            Message.sender_id != current_user.id,
            Message.status != "read",
        )
        .all()
    )
    if not messages:
        return {"message": "No unread messages"}

    for msg in messages:
        msg.status = "read"
    db.commit()
    return {"message": "All messages marked as read"}


@chat_router.get("/{chat_id}/messages/search")
async def search_messages(
    chat_id: str,
    keyword: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id, Message.content.ilike(f"%{keyword}%"))
        .all()
    )
    return {
        "messages": [
            {"message_id": msg.id, "content": msg.content, "timestamp": msg.timestamp}
            for msg in messages
        ]
    }


@chat_router.put("/{chat_id}/messages/{message_id}/pin")
async def pin_message(
    chat_id: str,
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = (
        db.query(Message)
        .filter(Message.id == message_id, Message.chat_id == chat_id)
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    message.pinned = True
    db.commit()
    return {"message": "Message pinned successfully"}


@chat_router.put("/{chat_id}/messages/{message_id}/unpin")
async def unpin_message(
    chat_id: str,
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = (
        db.query(Message)
        .filter(Message.id == message_id, Message.chat_id == chat_id)
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    message.pinned = False
    db.commit()
    return {"message": "Message unpinned successfully"}


@chat_router.post("/{chat_id}/messages/{message_id}/reactions")
async def react_to_message(
    chat_id: str,
    message_id: str,
    reaction: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = (
        db.query(Message)
        .filter(Message.id == message_id, Message.chat_id == chat_id)
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Assuming Reaction is a separate table
    reaction = Reaction(
        message_id=message_id, user_id=current_user.id, reaction=reaction
    )
    db.add(reaction)
    db.commit()
    db.refresh(reaction)

    return {"reaction_id": reaction.id, "message": "Reaction added successfully"}


@chat_router.get("/{chat_id}/messages/{message_id}/reactions")
async def get_message_reactions(
    chat_id: str,
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = (
        db.query(Message)
        .filter(Message.id == message_id, Message.chat_id == chat_id)
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    reactions = db.query(Reaction).filter(Reaction.message_id == message_id).all()
    return {
        "reactions": [
            {"user_id": reaction.user_id, "reaction": reaction.reaction}
            for reaction in reactions
        ]
    }


@chat_router.get("/{chat_id}/messages/{message_id}/detect_language")
async def detect_message_language(
    chat_id: str,
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = (
        db.query(Message)
        .filter(Message.id == message_id, Message.chat_id == chat_id)
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    language = detect(message.content)
    return {"message_id": message.id, "detected_language": language}


@chat_router.post("/{chat_id}/messages/{message_id}/translate")
async def translate_message(
    chat_id: str,
    message_id: str,
    target_language: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = (
        db.query(Message)
        .filter(Message.id == message_id, Message.chat_id == chat_id)
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    translated = GoogleTranslator(source="auto", target=target_language).translate(
        message.content
    )
    return {
        "original_message": message.content,
        "translated_message": translated,
        "target_language": target_language,
    }

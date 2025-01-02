from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from api.db.session import get_db
from api.v1.models.chat import Chat
from api.v1.models.contact import Contact
from api.v1.models.message import Message
from api.v1.models.reaction import Reaction
from api.v1.models.user import User
from api.v1.schemas.chat import ChatCreate, ChatResponse
from api.v1.schemas.message import MessageCreate
from api.utils.user import get_current_user
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

    # Create a new chat
    chat = Chat(user1_id=current_user.id, user2_id=recipient_id)
    db.add(chat)
    db.commit()
    db.refresh(chat)

    return {"chat_id": chat.id, "message": "Chat created successfully"}


@chat_router.get("/chats")
async def get_all_chats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    chats = (
        db.query(Chat)
        .filter((Chat.user1_id == current_user.id) | (Chat.user2_id == current_user.id))
        .all()
    )
    return {
        "chats": [
            {"chat_id": chat.id, "participants": [chat.user1_id, chat.user2_id]}
            for chat in chats
        ]
    }


@chat_router.get("/{chat_id}")
async def get_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = db.query(Chat).filter(Chat.id == chat_id ).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    return {
        "chat_id": chat.id,
        "participants": [chat.user1_id, chat.user2_id],
        "created_at": chat.created_at,
        "messages": [
            {
                "message_id": msg.id,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "status": msg.status,
            }
            for msg in chat.messages
        ],
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


@chat_router.websocket("/{chat_id}/ws")
async def websocket_endpoint(websocket: WebSocket, chat_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message from chat {chat_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


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

    # Broadcast the message via WebSocket
    await manager.broadcast(f"New message in chat {chat_id}: {message_data.content}")

    return {
        "message_id": message.id,
        "timestamp": message.timestamp,
        "message": "Message sent successfully",
    }


@chat_router.get("/{chat_id}/messages")
async def get_messages(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    return {
        "messages": [
            {
                "message_id": msg.id,
                "sender_id": msg.sender_id,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "status": msg.status,
            }
            for msg in chat.messages
        ]
    }


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

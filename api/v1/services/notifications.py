from fastapi import WebSocket, APIRouter
from typing import Dict

ws_router = APIRouter()

# To store active connections
connected_clients: Dict[int, WebSocket] = {}


@ws_router.websocket("/wss/notifications")
async def websocket_notifications(websocket: WebSocket):
    await websocket.accept()
    # print("New WebSocket connection established")
    user_id = (
        await websocket.receive_text()
    )  # Expecting the user to send their ID when connecting
    print(f"User ID received: {user_id}")

    # Add the user to the active connections
    connected_clients[user_id] = websocket

    try:
        while True:
            await websocket.receive_text()  # Keep the connection alive by receiving messages
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        connected_clients.pop(user_id, None)
        await websocket.close()


async def send_real_time_notification(user_id: str, message: str):
    """Send a real-time notification via WebSocket if the user is connected."""
    if user_id in connected_clients:
        websocket = connected_clients[user_id]
        await websocket.send_text(message)

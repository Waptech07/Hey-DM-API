import json
from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        # Mapping from chat_id to list of WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, chat_id: str, websocket: WebSocket):
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []
        self.active_connections[chat_id].append(websocket)
        print(f"WebSocket connection established for chat {chat_id}.")

    def disconnect(self, chat_id: str, websocket: WebSocket):
        if chat_id in self.active_connections:
            self.active_connections[chat_id].remove(websocket)
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]
        print(f"WebSocket connection disconnected for chat {chat_id}.")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, chat_id: str, message: str):
        if chat_id in self.active_connections:
            for connection in self.active_connections[chat_id]:
                await connection.send_text(message)
        print(f"Broadcasted message to chat {chat_id}: {message}")

# Create a single instance to be imported and used in your routes.
manager = ConnectionManager()

# import asyncio
# from datetime import datetime, timedelta
# import json
# from fastapi import WebSocket
# from typing import Dict, List


# class ConnectionManager:
#     def __init__(self):
#         self.active_connections: Dict[str, List[WebSocket]] = {}
#         self.connection_info: Dict[int, dict] = {}
#         self.heartbeat_task = asyncio.create_task(self._heartbeat_check())
    
    
#     async def _heartbeat_check(self):
#         while True:
#             await asyncio.sleep(30)
#             now = datetime.now()
#             for ws_id, info in list(self.connection_info.items()):
#                 if now - info["last_active"] > timedelta(seconds=60):
#                     print(f"Closing stale connection {ws_id}")
#                     await self._close_connection(info["chat_id"], ws_id)

#     async def _close_connection(self, chat_id: str, ws_id: int):
#         # Find the WebSocket object
#         for ws in self.active_connections.get(chat_id, []):
#             if id(ws) == ws_id:
#                 try:
#                     await ws.close()
#                 except Exception as e:
#                     print(f"Error closing connection: {str(e)}")
#                 self.disconnect(chat_id, ws)
#                 break

#     async def connect(self, chat_id: str, websocket: WebSocket):
#         try:
#             await websocket.accept()
#             if chat_id not in self.active_connections:
#                 self.active_connections[chat_id] = []
#             self.active_connections[chat_id].append(websocket)
#             self.connection_info[id(websocket)] = {
#                 "chat_id": chat_id,
#                 "last_active": datetime.now()
#             }
#             print(f"WebSocket connection established for chat {chat_id}")
#         except Exception as e:
#             print(f"Connection error: {str(e)}")
#             raise

#     def disconnect(self, chat_id: str, websocket: WebSocket):
#         try:
#             if chat_id in self.active_connections:
#                 self.active_connections[chat_id].remove(websocket)
#                 if not self.active_connections[chat_id]:
#                     del self.active_connections[chat_id]
#             if id(websocket) in self.connection_info:
#                 del self.connection_info[id(websocket)]
#             print(f"WebSocket connection disconnected for chat {chat_id}")
#         except Exception as e:
#             print(f"Disconnection error: {str(e)}")

#     async def broadcast(self, chat_id: str, message: str):
#         if chat_id in self.active_connections:
#             dead_connections = []
#             for connection in self.active_connections[chat_id]:
#                 try:
#                     await connection.send_text(message)
#                     self.connection_info[id(connection)]["last_active"] = datetime.now()
#                 except Exception as e:
#                     print(f"Broadcast error: {str(e)}")
#                     dead_connections.append(connection)
            
#             # Clean up dead connections
#             for connection in dead_connections:
#                 self.disconnect(chat_id, connection)

# # Create a single instance to be imported and used in your routes.
# manager = ConnectionManager()

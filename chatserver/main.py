from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            function getRandomName() {
                const names = ["Alice", "Bob", "Charlie"];
                const randomIndex = Math.floor(Math.random() * names.length);
                return names[randomIndex];
            }
            var preferred_name = getRandomName()
            var client_id = Date.now() // Unique ID for each client
            var room_id = "default" // Default room ID
            document.querySelector("#ws-id").textContent = preferred_name;
            var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}/${preferred_name}/testtoken/${room_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

valid_token = "testtoken"

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, token: str, room_id: str):
        if token == valid_token:
            await websocket.accept()
            self.active_connections.setdefault(room_id, []).append(websocket)
        else:
            pass

    def disconnect(self, websocket: WebSocket):
        for connections in self.active_connections.values():
            if websocket in connections:
                connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_to_room(self, message: str, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_text(message)

manager = ConnectionManager()

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws/{client_id}/{preferred_name}/{token}/{room_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int, preferred_name: str, token: str, room_id: str):
    await manager.connect(websocket, token=token, room_id=room_id)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"User: {preferred_name} wrote {data} in ", room_id)
            await manager.broadcast_to_room(f"{data}", room_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"{preferred_name} left the chat", room_id)

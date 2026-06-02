import argparse
import asyncio
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
import uvicorn

app = FastAPI(title="AetherStream Server")

class ConnectionManager:
    def __init__(self):
        # Maps WebSocket connection to its frame queue
        self.active_viewers = {}

    async def connect_viewer(self, websocket: WebSocket):
        await websocket.accept()
        # Set maxsize=1 so we only keep the latest frame (keeps latency low)
        self.active_viewers[websocket] = asyncio.Queue(maxsize=1)

    def disconnect_viewer(self, websocket: WebSocket):
        if websocket in self.active_viewers:
            del self.active_viewers[websocket]

    async def broadcast_frame(self, frame_bytes: bytes):
        if not self.active_viewers:
            return
        
        # Distribute the frame to all viewer queues
        for websocket, queue in list(self.active_viewers.items()):
            # If the queue is full, discard the old frame to maintain real-time low latency
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                await queue.put(frame_bytes)
            except Exception:
                # Handle any unexpected error during queue insertion
                pass

manager = ConnectionManager()

@app.get("/")
async def get_index():
    # Serve index.html statically from the root path
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "index.html not found"}

@app.websocket("/ws/sender")
async def websocket_sender(websocket: WebSocket):
    # TODO(security): Add token authentication if access controls are needed.
    await websocket.accept()
    print("Screen sender client connected!")
    try:
        while True:
            # Receive binary frame from sender
            data = await websocket.receive_bytes()
            # Broadcast the frame to all connected viewers
            await manager.broadcast_frame(data)
    except WebSocketDisconnect:
        print("Screen sender client disconnected.")
    except Exception as e:
        print(f"Error in sender connection: {e}")

@app.websocket("/ws/viewer")
async def websocket_viewer(websocket: WebSocket):
    # TODO(security): Add token authentication if access controls are needed.
    await manager.connect_viewer(websocket)
    print(f"Viewer connected! Total viewers: {len(manager.active_viewers)}")
    queue = manager.active_viewers[websocket]
    try:
        while True:
            # Wait for the next frame from the broadcast queue
            frame = await queue.get()
            # Send the binary frame to this viewer
            await websocket.send_bytes(frame)
    except WebSocketDisconnect:
        print("Viewer disconnected.")
    except Exception as e:
        print(f"Error sending frame to viewer: {e}")
    finally:
        manager.disconnect_viewer(websocket)
        print(f"Viewer removed. Total active viewers: {len(manager.active_viewers)}")

if __name__ == "__main__":
    # Render or other hostings define the PORT env variable and expect binding to 0.0.0.0
    env_port = os.environ.get("PORT")
    default_host = "0.0.0.0" if env_port else "127.0.0.1"
    default_port = int(env_port) if env_port else 8000

    parser = argparse.ArgumentParser(description="AetherStream Server")
    parser.add_argument("--host", type=str, default=default_host, 
                        help="Host address to bind the server to (default: 127.0.0.1 for local security, 0.0.0.0 for hosting)")
    parser.add_argument("--port", type=int, default=default_port, 
                        help="Port to run the server on (default: 8000)")
    args = parser.parse_args()

    # Warn about binding to 0.0.0.0 (skip warning if running on hosting environment)
    if args.host == "0.0.0.0" and not env_port:
        # TODO(security): Binding to 0.0.0.0 exposes the server to public network interfaces.
        # Ensure proper network access control (firewall/VPN) is active.
        print("\n" + "=" * 80)
        print("WARNING: Binding to 0.0.0.0 makes this server accessible to all network interfaces.")
        print("Ensure that your firewall or network setup secures this port from unauthorized access.")
        print("=" * 80 + "\n")

    print(f"Starting server on {args.host}:{args.port}...")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


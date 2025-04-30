import asyncio
import websockets
import json
import uuid
import socket

# Configuration
SERVER_URL = "wss://api.duckycart.me:8000/ws/cart"
CART_ID = str(uuid.uuid4())  # Unique cart id (you can make this static if you want)

# Helper: Get local IP for debug
def get_local_ip():
    return socket.gethostbyname(socket.gethostname())

async def handle_server_messages(websocket):
    async for message in websocket:
        print(f"[SERVER]: {message}")
        try:
            data = json.loads(message)
            command = data.get("command")

            if command == "start_session":
                await start_session()
            elif command == "end_session":
                await end_session()
            else:
                print(f"Unknown command: {command}")
        except Exception as e:
            print(f"Error processing message: {e}")

async def start_session():
    print("[ACTION]: Starting session...")
    # TODO: Add hardware start logic here (screen on, scanner on, etc.)
    # For example: turn on scale, display welcome message
    await asyncio.sleep(1)
    print("[ACTION]: Session started ✅")

async def end_session():
    print("[ACTION]: Ending session...")
    # TODO: Add hardware stop logic here (screen off, reset systems)
    await asyncio.sleep(1)
    print("[ACTION]: Session ended ✅")

async def send_status(websocket):
    while True:
        status_message = {
            "cart_id": CART_ID,
            "status": "online",
            "ip": get_local_ip()
        }
        await websocket.send(json.dumps(status_message))
        await asyncio.sleep(5)  # send status every 5 seconds

async def main():
    while True:
        try:
            print(f"Connecting to server at {SERVER_URL} ...")
            async with websockets.connect(SERVER_URL) as websocket:
                # Send initial hello with cart id
                await websocket.send(json.dumps({
                    "cart_id": CART_ID,
                    "status": "connected"
                }))
                print("[CONNECTED] Listening for commands...")

                # Run both sending status + handling server messages in parallel
                await asyncio.gather(
                    handle_server_messages(websocket),
                    send_status(websocket)
                )
        except Exception as e:
            print(f"[ERROR]: Connection lost: {e}. Retrying in 3 sec...")
            await asyncio.sleep(3)

if __name__ == "__main__":
    get_local_ip()  # Print local IP for debug
    print(f"Local IP: {get_local_ip()}")
    print(f"Cart ID: {CART_ID}")
    print("Starting cart client...")
    
    asyncio.run(main())

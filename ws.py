import os
import asyncio
import websockets

PORT = int(os.environ.get("PORT", 8765))  # Render ke PORT env var use karega

async def handler(websocket, path):
    print("✅ Incoming connection")
    async for message in websocket:
        if isinstance(message, bytes):
            print("🎧 Received audio chunk")
        else:
            print("📥 Metadata:", message)

async def main():
    async with websockets.serve(handler, "0.0.0.0", PORT):
        print(f"🚀 WebSocket server started on port {PORT}")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())

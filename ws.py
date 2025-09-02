import asyncio
import websockets

async def handler(websocket, path):
    print("✅ Incoming connection")
    async for message in websocket:
        if isinstance(message, bytes):
            print("🎧 Received audio chunk")
            # Forward to Whisper STT + n8n webhook here
        else:
            print("📥 Metadata:", message)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("🚀 WebSocket server started on port 8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())

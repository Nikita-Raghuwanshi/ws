import os
import asyncio
import websockets
from aiohttp import web

# Render ka PORT environment variable use karna hai
PORT = int(os.environ.get("PORT", 10000))

# WebSocket handler
async def handler(websocket):
    print("✅ Incoming WebSocket connection")
    async for message in websocket:
        if isinstance(message, bytes):
            print("🎧 Received audio chunk")
            # Yahan Whisper STT + n8n webhook call karna h
        else:
            print("📥 Metadata:", message)

# HTTP health check handler (for Render)
async def health(request):
    return web.Response(text="Server is running ✅")

async def main():
    # WebSocket server
    ws_server = await websockets.serve(handler, "0.0.0.0", PORT)
    
    # HTTP server (for health checks)
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    print(f"🚀 Server started on port {PORT} (WebSocket + HTTP)")

    await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())

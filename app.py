import asyncio
import websockets
from aiohttp import web   # extra library

async def handler(websocket, path):
    print("✅ Incoming connection")
    async for message in websocket:
        if isinstance(message, bytes):
            print("🎧 Received audio chunk")
            # Forward to Whisper STT + n8n webhook here
        else:
            print("📥 Metadata:", message)

# Health check ke liye simple HTTP route
async def health(request):
    return web.Response(text="OK")

async def main():
    # Start WebSocket server
   async with websockets.serve(handler, "0.0.0.0", 9000):


    # Start HTTP server for health check
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)  # alag port (10000)

    await asyncio.gather(ws_server, site.start())
    print("🚀 WebSocket server on :8765 and HTTP health check on :10000")

    await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())

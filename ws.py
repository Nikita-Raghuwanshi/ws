import os
import asyncio
import websockets
from aiohttp import web

PORT = int(os.environ.get("PORT", 10000))

async def handler(websocket, path):
    print("✅ Incoming connection")
    async for message in websocket:
        if isinstance(message, bytes):
            print("🎧 Received audio chunk")
        else:
            print("📥 Metadata:", message)

# ---------- HTTP Healthcheck ----------
async def health(request):
    return web.Response(text="Server is running ✅")

async def main():
    # WebSocket server
    ws_server = await websockets.serve(handler, "0.0.0.0", PORT)

    # HTTP server (for Render health check)
    app = web.Application()
    app.add_routes([web.get("/", health)])

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT+1)  # run on different port
    await site.start()

    print(f"🚀 WebSocket server on ws://0.0.0.0:{PORT}")
    print(f"🌍 HTTP health check on http://0.0.0.0:{PORT+1}")

    await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())

import os
import asyncio
import websockets
import requests
import json
from aiohttp import web

# 🔧 Configurable webhook URL via environment variable
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://n.ultracreation.in/webhook/knowlarity")
PORT = int(os.environ.get("PORT", 10000))

# 🔄 WebSocket handler
async def handler(websocket, path):
    print("🔗 Client connected")
    try:
        async for message in websocket:
            print(f"📩 Received: {message}")
            try:
                payload = json.loads(message)
                if isinstance(payload, dict) and "callerId" in payload:
                    for attempt in range(3):
                        try:
                            response = requests.post(N8N_WEBHOOK_URL, json={"payload": payload}, timeout=5)
                            if response.status_code == 200:
                                print(f"📤 Forwarded to n8n: {response.status_code}")
                                await websocket.send("✅ Acknowledged")  # 👈 Final fix: unblock client
                                break
                            else:
                                print(f"⚠️ Attempt {attempt+1} failed: {response.status_code}")
                        except Exception as e:
                            print(f"🔁 Retry {attempt+1} failed: {e}")
                else:
                    print("⚠️ Invalid payload structure")
                    await websocket.send("❌ Invalid payload")
            except Exception as e:
                print(f"❌ JSON parse error: {e}")
                await websocket.send("❌ JSON error")
    except Exception as e:
        print(f"❌ Connection error: {e}")

# 🌐 HTTP healthcheck for Render
async def health(request):
    return web.Response(text="Server is running ✅")

# 🚀 Main server startup
async def main():
    ws_server = await websockets.serve(handler, "0.0.0.0", PORT)

    app = web.Application()
    app.add_routes([web.get("/", health)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT + 1)
    await site.start()

    print(f"🚀 WebSocket server on ws://0.0.0.0:{PORT}")
    print(f"🌍 Healthcheck running on http://0.0.0.0:{PORT + 1}")

    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())

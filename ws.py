import os
import asyncio
import websockets
import requests
import json
from aiohttp import web
from datetime import datetime

# 🔧 Configurable webhook URL and port
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://n.ultracreation.in/webhook/knowlarity")
PORT = int(os.environ.get("PORT", 10000))

# 🧵 Active session log (optional)
active_sessions = {}

# 🔄 WebSocket handler
async def handler(websocket, path):
    print("🔗 Client connected:", websocket.remote_address)
    try:
        async for message in websocket:
            print(f"📩 Received: {message}")
            try:
                payload = json.loads(message)
                call_id = payload.get("call_id")
                event_type = payload.get("event_type")

                # ✅ Validate payload structure
                if not call_id or not event_type:
                    await websocket.send(json.dumps({"error": "❌ Missing call_id or event_type"}))
                    print("❌ Invalid payload structure")
                    continue

                # 🧠 Log session
                active_sessions[call_id] = {
                    "event": event_type,
                    "timestamp": datetime.now().isoformat()
                }

                # 📤 Forward to n8n
                response = None
                for attempt in range(3):
                    try:
                        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=5)
                        if response.status_code == 200:
                            print(f"✅ Forwarded to n8n: {response.status_code}")
                            break
                        else:
                            print(f"⚠️ Attempt {attempt+1} failed: {response.status_code}")
                    except Exception as e:
                        print(f"🔁 Retry {attempt+1} failed: {e}")

                # 🧪 Handle n8n response
                if response and response.status_code == 200:
                    try:
                        reply = response.json()
                        await websocket.send(json.dumps(reply))
                        print(f"📤 Sent to Knowlarity: {reply}")
                    except Exception as e:
                        await websocket.send(json.dumps({"error": "⚠️ Failed to parse n8n response"}))
                        print("⚠️ Response parse error:", e)
                else:
                    await websocket.send(json.dumps({"error": "❌ Webhook failed after retries"}))
                    print("❌ Webhook failure fallback sent")

            except json.JSONDecodeError as e:
                await websocket.send(json.dumps({"error": "❌ Invalid JSON"}))
                print("❌ JSON parse error:", e)

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

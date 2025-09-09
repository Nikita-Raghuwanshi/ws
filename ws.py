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
    print(f"🔗 Client connected from {websocket.remote_address} on path: {path}")
    if path != "/calls":
        await websocket.close(code=1008, reason="Invalid path")
        print("❌ Connection rejected: invalid path")
        return

    try:
        async for message in websocket:
            print(f"📩 Received: {message}")
            try:
                payload = json.loads(message)
                call_id = payload.get("call_id")
                event_type = payload.get("event_type")

                if not call_id or not event_type:
                    await websocket.send(json.dumps({"error": "❌ Missing call_id or event_type"}))
                    continue

                active_sessions[call_id] = {
                    "event": event_type,
                    "timestamp": datetime.now().isoformat()
                }

                response = None
                for attempt in range(3):
                    try:
                        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=5)
                        if response.status_code == 200:
                            break
                        else:
                            print(f"⚠️ Attempt {attempt+1} failed: {response.status_code}")
                    except Exception as e:
                        print(f"🔁 Retry {attempt+1} failed: {e}")

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

# 🌐 Healthcheck route
async def health(request):
    return web.Response(text="Server is running ✅")

# 🔊 Audio bridge endpoint for n8n
async def audio_bridge(request):
    try:
        data = await request.json()
        call_id = data.get("call_id")
        session_id = data.get("session_id")
        audio_base64 = data.get("audio_base64")

        if not call_id or not session_id or not audio_base64:
            return web.json_response({"error": "❌ Missing required fields"}, status=400)

        print(f"🎧 Audio received for call_id: {call_id}, session_id: {session_id}")
        print(f"📦 Audio length: {len(audio_base64)} bytes")

        return web.json_response({"status": "Audio received", "call_id": call_id})

    except Exception as e:
        print("❌ Error in audio bridge:", e)
        return web.json_response({"error": "❌ Internal server error"}, status=500)

# 🚀 Server startup
async def main():
    # WebSocket server (no path arg — validate manually)
    ws_server = await websockets.serve(handler, "0.0.0.0", PORT)

    # HTTP server for healthcheck and audio bridge
    app = web.Application()
    app.add_routes([
        web.get("/", health),
        web.post("/bridge/audio", audio_bridge)
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT + 1)
    await site.start()

    print(f"🚀 WebSocket server on ws://0.0.0.0:{PORT}/calls")
    print(f"🌍 Healthcheck at http://0.0.0.0:{PORT + 1}/")
    print(f"🔊 Audio bridge at http://0.0.0.0:{PORT + 1}/bridge/audio")

    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())

import os
import asyncio
import websockets
import requests
import json
import base64
from aiohttp import web
from datetime import datetime
import ffmpeg

# 🔧 Configurable webhook URL and port
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://n.ultracreation.in/webhook/knowlarity")
PORT = int(os.environ.get("PORT", 10000))

active_sessions = {}

# 🔄 WebSocket handler
async def handler(websocket, path):
    if path != "/calls":
        await websocket.close(code=1008, reason="Invalid path")
        return

    try:
        async for message in websocket:
            payload = json.loads(message)
            call_id = payload.get("call_id")
            event_type = payload.get("event_type")

            if not call_id or not event_type:
                await websocket.send(json.dumps({"error": "Missing call_id or event_type"}))
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
                except Exception:
                    continue

            if response and response.status_code == 200:
                reply = response.json()
                await websocket.send(json.dumps(reply))

                audio_base64 = reply.get("audio_base64")
                if audio_base64:
                    mp3_bytes = base64.b64decode(audio_base64)
                    pcm_path = f"{call_id}.pcm"

                    process = (
                        ffmpeg
                        .input('pipe:0')
                        .output(pcm_path, format='s16le', acodec='pcm_s16le', ac=1, ar='8000')
                        .run_async(pipe_stdin=True)
                    )
                    process.stdin.write(mp3_bytes)
                    process.stdin.close()
                    process.wait()

                    with open(pcm_path, "rb") as f:
                        while chunk := f.read(320):
                            await websocket.send(chunk)
                            await asyncio.sleep(0.02)
            else:
                await websocket.send(json.dumps({"error": "Webhook failed"}))
    except Exception:
        pass

# 🌐 HTTP routes
async def health(request):
    return web.Response(text="Server is running ✅")

async def audio_bridge(request):
    try:
        data = await request.json()
        call_id = data.get("call_id")
        session_id = data.get("session_id")
        audio_base64 = data.get("audio_base64")

        if not call_id or not session_id or not audio_base64:
            return web.json_response({"error": "Missing fields"}, status=400)

        return web.json_response({"status": "Audio received", "call_id": call_id})
    except Exception:
        return web.json_response({"error": "Internal error"}, status=500)

# ✅ Startup logic
async def start_servers():
    app = web.Application()
    app.add_routes([
        web.get("/", health),
        web.post("/bridge/audio", audio_bridge)
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    await websockets.serve(handler, "0.0.0.0", PORT + 1)

    print(f"🌍 HTTP server running on http://0.0.0.0:{PORT}/")
    print(f"🚀 WebSocket server on ws://0.0.0.0:{PORT + 1}/calls")

# ✅ Entry point for Render
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_servers())
    loop.run_forever()

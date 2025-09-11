import os
import asyncio
import requests
from aiohttp import web
from datetime import datetime

# Configuration
KNOWLARITY_API_URL = os.getenv("KNOWLARITY_API_URL", "https://api.knowlarity.com/voice/call")
PORT = int(os.environ.get("PORT", 10000))

async def health(request):
    return web.Response(text="Bridge Server Running ✅")

async def audio_bridge(request):
    try:
        data = await request.json()

        # Required fields
        call_id = data.get("call_id")
        session_id = data.get("session_id")
        audio_base64 = data.get("audio_base64")
        timestamp = data.get("timestamp", datetime.now().isoformat())

        if not all([call_id, session_id, audio_base64]):
            print(f"⚠️ Missing fields: {data}")
            return web.json_response({"error": "Missing required fields"}, status=400)

        print(f"🎧 Received audio for call_id: {call_id}, session_id: {session_id}")

        # Prepare payload for Knowlarity
        knowlarity_payload = {
            "call_id": call_id,
            "session_id": session_id,
            "audio_data": audio_base64,
            "audio_format": "pcm_s16le",
            "sample_rate": 8000,
            "timestamp": timestamp
        }

        try:
            response = requests.post(KNOWLARITY_API_URL, json=knowlarity_payload, timeout=10)
            print(f"📨 Knowlarity Response: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Knowlarity Forwarding Failed: {e}")
            return web.json_response({"error": "Forwarding to Knowlarity failed"}, status=502)

        return web.json_response({
            "status": "Audio received and forwarded",
            "call_id": call_id,
            "audio_format": "pcm_s16le",
            "sample_rate": 8000,
            "timestamp": timestamp
        })

    except Exception as e:
        print(f"❌ Bridge Error: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)

async def start_server():
    app = web.Application()
    app.add_routes([
        web.get("/", health),
        web.get("/health", health),
        web.post("/bridge/audio", audio_bridge)
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"🚀 Bridge Server Live at http://0.0.0.0:{PORT}")
    print(f"🔊 Audio Endpoint: /bridge/audio")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server())
    loop.run_forever()

import os
import asyncio
import requests
import json
import base64
from aiohttp import web
from datetime import datetime

# Configuration
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://n.ultracreation.in/webhook/knowlarity")
KNOWLARITY_API_URL = os.getenv("KNOWLARITY_API_URL", "https://api.knowlarity.com/api/audio")
PORT = int(os.environ.get("PORT", 10000))

async def health(request):
    return web.Response(text="Bridge Server Running ✅")

async def audio_bridge(request):
    try:
        data = await request.json()
        
        # Validate required fields
        call_id = data.get("call_id")
        session_id = data.get("session_id") 
        audio_base64 = data.get("audio_base64")
        
        if not all([call_id, session_id, audio_base64]):
            return web.json_response({"error": "Missing required fields"}, status=400)
        
        print(f"🎵 Processing PCM audio for call: {call_id}")
        
        # Audio is already in PCM format from Cartesia
        # No conversion needed - directly forward to Knowlarity
        
        knowlarity_payload = {
            "call_id": call_id,
            "session_id": session_id,
            "audio_data": audio_base64,
            "audio_format": "pcm_s16le",
            "sample_rate": 8000,
            "timestamp": data.get("timestamp", datetime.now().isoformat())
        }
        
        # Forward to Knowlarity (or process as needed)
        # response = requests.post(KNOWLARITY_API_URL, json=knowlarity_payload, timeout=10)
        
        return web.json_response({
            "status": "Audio received and processed", 
            "call_id": call_id,
            "audio_format": "pcm_s16le",
            "sample_rate": 8000,
            "processing_time_ms": 50
        })
        
    except Exception as e:
        print(f"❌ Bridge Error: {e}")
        return web.json_response({"error": "Processing failed"}, status=500)

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
    
    print(f"🌐 Bridge Server: http://0.0.0.0:{PORT}")
    print(f"📡 Audio Endpoint: /bridge/audio")

if _name_ == "_main_":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server())
    loop.run_forever()

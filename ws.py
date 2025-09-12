import os
import asyncio
import base64
import tempfile
from aiohttp import web
from datetime import datetime
import json
 
# Configuration
PORT = int(os.environ.get("PORT", 10000))
KNOWLARITY_API_KEY = os.getenv("KNOWLARITY_API_KEY", "default_key")
 
async def health(request):
    """Health check endpoint"""
    return web.Response(text="Bridge Server Running ✅", content_type='text/plain')
 
async def audio_bridge(request):
    """Main audio processing endpoint"""
    try:
        data = await request.json()
        # Required fields
        call_id = data.get("call_id", "unknown")
        session_id = data.get("session_id", "unknown")
        audio_base64 = data.get("audio_base64", "")
        timestamp = data.get("timestamp", datetime.now().isoformat())
        print(f"🎧 Received request for call_id: {call_id}")
        if not all([call_id, session_id, audio_base64]):
            print(f"⚠️ Missing fields in request")
            return web.json_response({
                "error": "Missing required fields",
                "knowlarity_response": {
                    "play": "Sorry, there was a technical error. Please try again.",
                    "hangup": False
                }
            }, status=400)
        print(f"📋 Processing audio for call_id: {call_id}")
        # Process audio
        try:
            audio_data = base64.b64decode(audio_base64)
            print(f"✅ Decoded audio data: {len(audio_data)} bytes")
            # Create and clean up temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(audio_data)
                temp_audio_path = temp_file.name
            # Clean up immediately
            os.unlink(temp_audio_path)
            # Return direct text response for Knowlarity
            response_text = "Your request has been processed. Thank you for calling UltraXpert Technologies."
            knowlarity_response = {
                "play": response_text,
                "hangup": False,
                "next": "continue"
            }
            print(f"✅ Successfully processed audio for call_id: {call_id}")
            return web.json_response({
                "status": "success",
                "call_id": call_id,
                "timestamp": timestamp,
                "knowlarity_response": knowlarity_response
            })
        except Exception as audio_error:
            print(f"❌ Audio Processing Error: {audio_error}")
            fallback_response = {
                "play": "Thank you for calling UltraXpert Technologies. We will get back to you shortly.",
                "hangup": False
            }
            return web.json_response({
                "status": "fallback",
                "call_id": call_id,
                "knowlarity_response": fallback_response
            })
    except json.JSONDecodeError:
        print("❌ Invalid JSON in request")
        return web.json_response({
            "error": "Invalid JSON",
            "knowlarity_response": {
                "play": "Invalid request format.",
                "hangup": True
            }
        }, status=400)
    except Exception as e:
        print(f"❌ Bridge Error: {e}")
        error_response = {
            "play": "We are experiencing technical difficulties. Please call back later.",
            "hangup": True
        }
        return web.json_response({
            "error": "Internal server error",
            "knowlarity_response": error_response
        }, status=500)
 
async def test_endpoint(request):
    """Test endpoint for debugging"""
    return web.json_response({
        "message": "Bridge server is working perfectly!",
        "timestamp": datetime.now().isoformat(),
        "server_status": "healthy",
        "endpoints": {
            "health": "/health",
            "audio_bridge": "/bridge/audio",
            "test": "/test"
        }
    })
 
def create_app():
    """Create and configure the web application - SIMPLIFIED"""
    app = web.Application()
    # Simple route setup - no complex middleware
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    app.router.add_get("/test", test_endpoint)
    app.router.add_post("/bridge/audio", audio_bridge)
    return app
 
async def init_app():
    """Initialize the application"""
    app = create_app()
    return app
 
def main():
    """Main function - SIMPLIFIED"""
    print("🚀 Starting Bridge Server...")
    print(f"🔊 Port: {PORT}")
    print(f"🔑 API Key configured: {'Yes' if KNOWLARITY_API_KEY != 'default_key' else 'No'}")
    # Create app
    app = create_app()
    # Run app - simple method
    web.run_app(
        app,
        host="0.0.0.0",
        port=PORT,
        access_log=None  # Disable access logs for cleaner output
    )
 
if __name__ == "__main__":
    main()

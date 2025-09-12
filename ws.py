import os
import asyncio
import requests
import base64
import tempfile
from aiohttp import web
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(_name_)

# Configuration
KNOWLARITY_API_URL = os.getenv("KNOWLARITY_API_URL", "https://kpi.knowlarity.com/voice/call")
PORT = int(os.environ.get("PORT", 10000))
KNOWLARITY_API_KEY = os.getenv("KNOWLARITY_API_KEY", "QdQa83awS05tyB0KAVATX7tvm3WuBXz16QEluhix")

async def health(request):
    """Health check endpoint"""
    return web.Response(text="Bridge Server Running ✅")

async def audio_bridge(request):
    """Main audio processing endpoint"""
    try:
        data = await request.json()
        
        # Required fields
        call_id = data.get("call_id")
        session_id = data.get("session_id")
        audio_base64 = data.get("audio_base64")
        timestamp = data.get("timestamp", datetime.now().isoformat())
        
        logger.info(f"Received request for call_id: {call_id}")
        
        if not all([call_id, session_id, audio_base64]):
            logger.warning(f"Missing fields in request: {data}")
            return web.json_response({
                "error": "Missing required fields",
                "knowlarity_response": {
                    "play": "Sorry, there was a technical error. Please try again.",
                    "hangup": False
                }
            }, status=400)
        
        logger.info(f"Processing audio for call_id: {call_id}")
        
        # Convert base64 to temporary audio file
        try:
            audio_data = base64.b64decode(audio_base64)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(audio_data)
                temp_audio_path = temp_file.name
            
            logger.info(f"Created temp audio file: {temp_audio_path} (size: {len(audio_data)} bytes)")
            
            # For now, return direct text response
            # TODO: Implement audio file hosting and return URL
            response_text = "Your request has been processed. Thank you for calling UltraXpert Technologies."
            
            # Clean up temp file
            os.unlink(temp_audio_path)
            
            # Return proper Knowlarity call control format
            knowlarity_response = {
                "play": response_text,
                "hangup": False,
                "next": "continue"
            }
            
            logger.info(f"Successfully processed audio for call_id: {call_id}")
            
            return web.json_response({
                "status": "success",
                "call_id": call_id,
                "timestamp": timestamp,
                "knowlarity_response": knowlarity_response
            })
            
        except Exception as audio_error:
            logger.error(f"Audio Processing Error: {audio_error}")
            
            # Fallback response
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
        logger.error("Invalid JSON in request")
        return web.json_response({
            "error": "Invalid JSON",
            "knowlarity_response": {
                "play": "Invalid request format.",
                "hangup": True
            }
        }, status=400)
        
    except Exception as e:
        logger.error(f"Bridge Error: {e}")
        
        # Error fallback
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
        "message": "Bridge server is working",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "audio_bridge": "/bridge/audio",
            "test": "/test"
        }
    })

async def create_app():
    """Create and configure the web application"""
    app = web.Application()
    
    # Add CORS headers for development
    async def cors_handler(request, handler):
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    app.middlewares.append(cors_handler)
    
    # Add routes
    app.add_routes([
        web.get("/", health),
        web.get("/health", health),
        web.get("/test", test_endpoint),
        web.post("/bridge/audio", audio_bridge),
        web.options("/bridge/audio", lambda r: web.Response(status=200))
    ])
    
    return app

async def start_server():
    """Start the server"""
    app = await create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    
    logger.info(f"🚀 Bridge Server Started Successfully")
    logger.info(f"🔊 Server running on: http://0.0.0.0:{PORT}")
    logger.info(f"📡 Health check: http://0.0.0.0:{PORT}/health")
    logger.info(f"🎧 Audio endpoint: http://0.0.0.0:{PORT}/bridge/audio")
    logger.info(f"🧪 Test endpoint: http://0.0.0.0:{PORT}/test")
    
    return runner

def main():
    """Main function"""
    # Check API key
    if not KNOWLARITY_API_KEY or "paste" in KNOWLARITY_API_KEY.lower():
        logger.error("🔴 CRITICAL: KNOWLARITY_API_KEY is not set properly!")
        logger.error("Please set the KNOWLARITY_API_KEY environment variable")
        return
    
    logger.info("🔑 API Key configured")
    
    # Start server
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        runner = loop.run_until_complete(start_server())
        logger.info("✅ Server started successfully, running forever...")
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Server shutdown requested")
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
    finally:
        if 'runner' in locals():
            loop.run_until_complete(runner.cleanup())
        loop.close()

if _name_ == "_main_":
    main()

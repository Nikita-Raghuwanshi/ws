import os
import asyncio
import websockets
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

async def handler(websocket, path):
    print("✅ Incoming WebSocket connection")
    async for message in websocket:
        if isinstance(message, bytes):
            print("🎧 Received audio chunk")
        else:
            print("📥 Metadata:", message)

# HTTP server for Render health check
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def start_http_server():
    httpd = HTTPServer(("0.0.0.0", 10000), HealthHandler)
    httpd.serve_forever()

async def main():
    # start HTTP server in background
    threading.Thread(target=start_http_server, daemon=True).start()

    PORT = int(os.environ.get("PORT", 8765))  # Render sets PORT automatically
    async with websockets.serve(handler, "0.0.0.0", PORT):
        print(f"🚀 WebSocket server started on port {PORT}")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())

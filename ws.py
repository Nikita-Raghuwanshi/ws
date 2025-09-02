import asyncio
import websockets
import requests
import json
import os

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://n.ultracreation.in/webhook/knowlarity")

async def handler(websocket):
    async for message in websocket:
        print(f"📩 Received: {message}")
        try:
            payload = json.loads(message)
            response = requests.post(N8N_WEBHOOK_URL, json={"payload": payload})
            print(f"📤 Forwarded to n8n: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8080):
        print("✅ WebSocket bridge running on ws://0.0.0.0:8080")
        await asyncio.Future()  # Keeps the server running

if __name__ == "__main__":
    asyncio.run(main())

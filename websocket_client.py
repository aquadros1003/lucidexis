import asyncio
import json
import sys

import websockets


async def chat_client(ws_url: str, token: str) -> None:
    url = f"{ws_url}?token={token}"
    print(f"Connecting to {ws_url}...")
    try:
        async with websockets.connect(url) as websocket:
            print("Connected! Type your messages (Ctrl+C to exit)\n")
            async def receive_messages():
                try:
                    async for message in websocket:
                        data = json.loads(message)
                        if data["type"] == "message":
                            msg = data["message"]
                            role = msg["role"].upper()
                            content = msg["content"]
                            print(f"\n[{role}]: {content}")
                            if role == "ASSISTANT":
                                print("\nYou: ", end="", flush=True)
                        elif data["type"] == "error":
                            print(f"\n[ERROR]: {data['error']}")
                except websockets.exceptions.ConnectionClosed:
                    print("\nConnection closed by server")
                except Exception as e:
                    print(f"\nError receiving message: {e}")
            receive_task = asyncio.create_task(receive_messages())
            try:
                while True:
                    print("You: ", end="", flush=True)
                    message = await asyncio.get_event_loop().run_in_executor(
                        None, sys.stdin.readline
                    )
                    message = message.strip()
                    if not message:
                        continue
                    await websocket.send(json.dumps({"content": message}))
            except KeyboardInterrupt:
                print("\n\nExiting...")
                receive_task.cancel()
    except websockets.InvalidStatus as e:
        print(f"Connection failed: {e}")
        print("Make sure the token is valid and server is running")
    except Exception as e:
        print(f"Error: {e}")


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python websocket_client.py <conversation_id> <token>")
        print("\nExample:")
        print("  python websocket_client.py <uuid> <jwt_token>")
        print("\nTo get a token, first login:")
        print("  curl -X POST http://localhost:8000/api/v1/login/access-token \\")
        print("    -d 'username=admin@example.com&password=yourpassword'")
        sys.exit(1)
    conversation_id = sys.argv[1]
    token = sys.argv[2]
    ws_url = f"ws://localhost:8000/api/v1/chat/ws/{conversation_id}"
    try:
        asyncio.run(chat_client(ws_url, token))
    except KeyboardInterrupt:
        print("\nGoodbye!")


if __name__ == "__main__":
    main()

import asyncio
from websockets.sync.client import connect


def hello():
    with connect("ws://localhost:8765") as websocket:
        websocket.send("Hello World!")
        message = websocket.recv()
        print(f"Recieved: {message}")


hello()
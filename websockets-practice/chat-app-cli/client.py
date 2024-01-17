import asyncio
from websockets.sync.client import ClientConnection
from websockets import connect
import pickle
from aioconsole import ainput


async def handle_recieve(ws: ClientConnection):
    while True:
        message = await ws.recv()
        if type(message) is str:
            print(f"<<< {message}")
        elif type(message) is bytes:
            message = pickle.loads(message)
            print(f"<<< {message.message} <<< {message.sender.name}")
        

async def handle_get_users(ws: ClientConnection):
    operation: str = await ainput()
    message = operation.strip()
    if message == "list":
        await ws.send(message)
    return


async def handle_message_to_user(ws: ClientConnection):
    operation: str = await ainput()
    try:
        if len(operation.split("->")) == 2:
            await ws.send(operation)
    except ValueError:
        ...
    return


async def main():
    uri = "ws://127.0.0.1:8765"
    async with connect(uri) as websocket:
        username = input("Provide your username: ")
        register_message = "username=" + username
        await websocket.send(register_message)
        # Getting either success code or registration failure, after which the server will automatically close this connection
        await websocket.recv()

        # Start listening for eventual messages
        asyncio.create_task(handle_recieve(websocket))
        print("Type:\nlist - to list members of this lobby;\nreceiver_username -> your_message")
        while True:
            await asyncio.gather(
                handle_get_users(websocket), handle_message_to_user(websocket)
                )
        

        

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())

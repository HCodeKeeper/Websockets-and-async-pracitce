import asyncio
from websockets.server import serve
from websockets import WebSocketServerProtocol
from dataclasses import dataclass
from queue import Queue
import pickle


MAX_USER_MESSAGE_POOL_SIZE = 200

connected_users = set()


class MessageParser():
    @staticmethod
    def get_username_from_registration(message: str):
        try:
            message_parts = message.split("=")
        except ValueError as e:
            raise BadOperation("Operation syntax didn't have a '=' symbol") from e
        if message_parts[0] == "username":
            username =  message_parts[1]
            if username != '':
                return username
            raise ValueError("Username wasn't provided: username=''")
        else:
            raise ValueError("Key 'username' wasn't found. Message should look like 'username=your_username'")
    
    @staticmethod
    def get_user_and_message_to_send(message: str) -> list:
        if "->" in message:
            message_parts = message.split("->", 1)
            print(message, message_parts)
        else:
            raise BadOperation("Operation syntax didn't have a '=' symbol")
        if message_parts[0] == "username":
            username =  message_parts[0].strip()
            if username:
                message_to_send = message_parts[1].strip()
                if message_to_send:
                    user = get_user(username)
                    return (user, message_to_send)
            raise ValueError("Username wasn't provided")
        else:
            raise ValueError("Key 'username' wasn't found.")


class User:
    def __init__(self, name:str, websocket: WebSocketServerProtocol):
        self._name = None
        self.name = name
        self.__inbox_pool = UserMessagePool()
        self._inbox_lock = asyncio.Lock()
        self._inbox_event = asyncio.Event()
        
        self._websocket_protocol: WebSocketServerProtocol = websocket

    @property
    def websocket(self):
        return self._websocket_protocol

    @property
    def inbox_pool(self):
        return self.__inbox_pool

    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, val: str):
        val = val.strip()
        self._name = val
    
    @staticmethod
    def instantiate_from_message(message:str, websocket: WebSocketServerProtocol):
        name = MessageParser.get_username_from_registration(message)
        return __class__(name, websocket)
    

    def notify_inbox(self):
        self._inbox_event.set()

    async def wait_for_inbox_notification(self, timeout=None):
        async with self._inbox_lock:
            await asyncio.wait_for(self._inbox_event.wait(), timeout)
            self._inbox_event.clear()
    

class UserMessage:
    def __init__(self, sender: User, message: str, reciever: User) -> None:
        self.sender = sender
        self.message = message
        self.reciever = reciever


class UserMessagePool:
    def __init__(self) -> None:
        self.pool = Queue(MAX_USER_MESSAGE_POOL_SIZE)

    def add(self, message: UserMessage):
        self.pool.put(message)
        message.reciever.notify_inbox()
    
    def pull(self):
        return self.pool.get_nowait()
    
    def pull_all(self) -> Queue:
        returned_queue = Queue()
        while not self.pool.empty():
            returned_queue.put(self.pool.get_nowait())
        return returned_queue


class UserException(Exception):
    def __init__(self, message, *args: object) -> None:
            super().__init__(*args)
            self.message = message


class BadOperation(UserException):
    ...


class CouldntRegisterAUser(Exception):
    ...


class CouldntFindAUser(Exception):
    ...


async def handle_registration(websocket: WebSocketServerProtocol, message):
    try:
        user = User.instantiate_from_message(message, websocket)
        connected_users.add(user)
        await websocket.send(f"Connection for user {user.name} has been established")
        return user
    except ValueError|BadOperation as e:
        error_message = e.args[0]
        await websocket.send(error_message)
        raise CouldntRegisterAUser(f"Invalid message for {websocket.remote_address[0]}. Message: {error_message}") from e


def list_users():
    return "; ".join([connected_user.name for connected_user in connected_users])


def get_user(username:str):
    username = username.strip()
    for connected_user in connected_users:
        if connected_user.name == username:
            return connected_user
    raise CouldntFindAUser(f"User with name: {username} is abscent")


async def handle_receive_user_to_user_message(websocket: WebSocketServerProtocol, message, sender: User):
    try:
        user: User = None
        user, message_to_send = MessageParser.get_user_and_message_to_send(message)
    except ValueError as e:
        await websocket.send(e.args[0])
        return
    except BadOperation as e:
        return
    user.inbox_pool.put(UserMessage(sender, message_to_send, user))


# Has to be run outside the message loop
async def handle_respond_user_to_user_message(receiver: User):
    await receiver.wait_for_inbox_notification()
    message_pool = receiver.inbox_pool
    while not message_pool.pool.empty():
        await receiver.websocket.send(message_pool.pull())


async def broad_handler(websocket: WebSocketServerProtocol):
    is_first_message = True
    user: User = None
    async for message in websocket:
        if is_first_message:
            try:
                user = await handle_registration(websocket, message)
            except CouldntRegisterAUser as e:
                print(e.message)
                print("Closing connection for this user")
                await websocket.close()
                return
            
            asyncio.create_task(handle_respond_user_to_user_message(user))
            is_first_message = False
        else:
            try:
                await handle_receive_user_to_user_message(websocket, message, user)
            except BadOperation as e:
                ...


start_server = serve(broad_handler, "127.0.0.1", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
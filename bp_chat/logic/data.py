from datetime import datetime


class ServerData:

    users: {int: 'User'}
    chats: {int: 'Chat'}

    def __init__(self, users, chats):
        self.users = users
        self.chats = chats


class User:

    _id: int
    name: str

    def __init__(self, id, name):
        self._id = id
        self.name = name


class Chat:

    PRIVATE = 0
    GROUP = 1

    _id: int
    _type: int
    title: str
    users: ['User']
    messages: {int: 'Message'}

    def __init__(self, id, title, users, messages, chat_type=GROUP):
        self._id = id
        self.title = title
        self.users = users
        self.messages = messages
        self._type = chat_type

    @property
    def id(self):
        return self._id

    @property
    def type(self):
        return self._type

    def get_last_message(self):
        if len(self.messages) == 0:
            return None
        keys = list(self.messages.keys())
        key = max(keys)
        return self.messages[key]


class Message:

    _id: int
    sender: User
    chat: Chat
    text: str
    datetime: datetime

    def __init__(self, id, sender, chat, text, datetime):
        self._id = id
        self.sender = sender
        self.chat = chat
        self.text = text
        self.datetime = datetime

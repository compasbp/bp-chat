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

    _id: int
    title: str
    users: ['User']
    messages: {int: 'Message'}

    def __init__(self, id, title, users, messages):
        self._id = id
        self.title = title
        self.users = users
        self.messages = messages


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

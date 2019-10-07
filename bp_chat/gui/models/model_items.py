from ..models.list_model import ListModelItem
from .funcs import item_from_object


class UserItem(ListModelItem):

    def __init__(self, user):
        self.user = user

    def getName(self):
        return self.user.name

    def getSecondText(self):
        return 'Some text...'

    def getTimeString(self):
        return '11:00'

    def getPixmap(self):
        return None

    def getBadgesCount(self):
        return 3


class ChatItem(ListModelItem):

    def __init__(self, chat):
        self.chat = chat

    def getName(self):
        return self.chat.title

    def getSecondText(self):
        message = self.chat.get_last_message()
        if message:
            return message.text
        else:
            return ''

    def getTimeString(self):
        return '11:00'

    def getPixmap(self):
        return None

    def getBadgesCount(self):
        return 3


class MessageItem(ListModelItem):

    def __init__(self, message):
        self.message = message

    def getName(self):
        user = item_from_object(self.message.sender, UserItem)
        return user.getName()

    def getSecondText(self):
        return self.message.text

    def getTimeString(self):
        return '11:00'

    def getPixmap(self):
        return None

    def getBadgesCount(self):
        return 0



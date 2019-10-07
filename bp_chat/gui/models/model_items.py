from ..models.list_model import ListModelItem


class ChatItem(ListModelItem):

    def __init__(self, chat):
        self.chat = chat

    def getName(self):
        return self.chat.title

    def getSecondText(self):
        return 'Some text...'

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
        return self.message.sender

    def getSecondText(self):
        return self.message.text

    def getTimeString(self):
        return '11:00'

    def getPixmap(self):
        return None

    def getBadgesCount(self):
        return 0



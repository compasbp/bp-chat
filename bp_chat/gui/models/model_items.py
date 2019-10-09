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

    COLORS = (
        '#bbe7b9', '#7eaae0', '#fbdaa0', '#e7e6bc', '#f4bbb4', '#9cbdf4', '#a1b2b7'
    )
    __LAST_COLOR = -1

    def __init__(self, chat):
        self.chat = chat

        ChatItem.__LAST_COLOR += 1
        if ChatItem.__LAST_COLOR > 6:
            ChatItem.__LAST_COLOR = 0

        self.chat_color = ChatItem.COLORS[ChatItem.__LAST_COLOR]

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
        return 'group'

    def getBadgesCount(self):
        return 3

    def getColor(self):
        return self.chat_color


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



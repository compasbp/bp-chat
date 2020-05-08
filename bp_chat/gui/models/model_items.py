from datetime import datetime

from ..models.list_model import ListModelItem
from .funcs import item_from_object


class ColoredItem:
    COLORS = (
        '#bbe7b9', '#7eaae0', '#fbdaa0', '#e7e6bc', '#f4bbb4', '#9cbdf4', '#a1b2b7'
    )
    __LAST_COLOR = -1

    @classmethod
    def get_new_color(cls):
        cls.__LAST_COLOR += 1
        if cls.__LAST_COLOR > 6:
            cls.__LAST_COLOR = 0
        return ChatItem.COLORS[cls.__LAST_COLOR]


class UserItem(ListModelItem, ColoredItem):

    def __init__(self, user):
        self.user = user
        self.color = self.get_new_color()

    @property
    def item(self):
        return self.user

    def getName(self):
        return self.user.name

    def getSecondText(self):
        return 'Some text...'

    def getTimeString(self):
        return '11:00'

    def getPixmap(self):
        return 'user'

    def getBadgesCount(self):
        return 3

    def getColor(self):
        return self.color


class ChatItem(ListModelItem, ColoredItem):

    def __init__(self, chat):
        self.chat = chat
        self.color = self.get_new_color()

    @property
    def item(self):
        return self.chat

    def getName(self):
        return self.chat.title

    def getNick(self):
        return self.chat.getLogin()

    def getSecondText(self):
        message = self.chat.get_last_message()
        if message:
            text = message.text
            return text
        else:
            return ''

    def getTimeString(self):
        message = self.chat.get_last_message()
        if message:
            item = item_from_object(message, MessageItem)
            return item.getTimeString()
        return None

    def getPixmap(self):
        return 'group'

    def getBadgesCount(self):
        return 3

    def getColor(self):
        chat_color = getattr(self.chat, 'chat_color', None) if self.chat else None
        return chat_color or self.color

    def getStatusColor(self):
        if self.chat.is_private():
            if self.chat.user.is_online():
                if self.chat.user.is_sleep():
                    return (249, 177, 53)
                else:
                    return (84, 213, 84)
            else:
                return (190, 190, 190)
        return None

    def isSelectedItem(self):
        return self.chat.is_selected_chat()


class MessageItem(ListModelItem):

    def __init__(self, message):
        self.message = message

    @property
    def item(self):
        return self.message

    @property
    def sender_item(self) -> UserItem:
        item = item_from_object(self.message.sender, UserItem)
        if not item:
            item = NullItem
        return item

    def getName(self):
        return self.sender_item.getName()

    def getSecondText(self):
        return self.message.text

    def getTimeString(self):
        return self.getTimeStringBase(True)

    def getTimeStringBase(self, full):
        localTime = "--:--"
        if self.message.datetime != None:
            if full:
                format = "%d.%m.%Y %H:%M" # :ss
            else:
                format = "%d.%m.%Y"

            today = datetime.now()
            year_today = today.year
            month_today = today.month
            day_today = today.day

            timeday = self.message.datetime #datetime.fromtimestamp(self._time)
            year = timeday.year
            month = timeday.month
            day = timeday.day
            if year == year_today and month == month_today and day == day_today:
                format = "%H:%M" # :ss
            localTime = timeday.strftime(format)
        return localTime

    def getPixmap(self):
        return self.sender_item.getPixmap()

    def getBadgesCount(self):
        return 0

    def getColor(self):
        return self.sender_item.getColor()


# FIXME
class NullItem:

    @classmethod
    def getName(cls):
        return "Null"

    @classmethod
    def getPixmap(cls):
        return None

    @classmethod
    def getColor(cls):
        return "#ffffff"

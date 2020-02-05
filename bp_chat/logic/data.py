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

    @property
    def id(self):
        return self._id


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
    file = None
    _delivered = True  # delivered?

    _selected_text = None

    @property
    def id(self):
        return self._id

    @property
    def selected_text(self):
        return self._selected_text

    def set_selected_text(self, val):
        if self._selected_text != val:
            #print('NEW sel text: {}'.format(val))
            self._selected_text = val

    def __init__(self, id, sender, chat, text, datetime):
        self._id = id
        self.sender = sender
        self.chat = chat
        self.text = text
        self.datetime = datetime

    @property
    def sender_id(self):
        return self.sender.id

    def setDelivered(self, delivered):
        self._delivered = delivered

    def getDelivered(self):
        return self._delivered

    def getTimeString(self):
        return self.getTimeStringBase(True)

    def getTimeStringShort(self):
        return self.getTimeStringBase(False)

    def getTimeStringBase(self, full):
        #Calendar cal = Calendar.getInstance()
        #TimeZone tz = cal.getTimeZone()
        localTime = "--:--"
        if self.datetime != None:
            if full:
                format = "%d.%m.%Y %H:%M" # :ss
            else:
                format = "%d.%m.%Y"

            today = datetime.now()
            year_today = today.year
            month_today = today.month
            day_today = today.day

            timeday = self.datetime #datetime.fromtimestamp(self._time)
            year = timeday.year
            month = timeday.month
            day = timeday.day
            if year == year_today and month == month_today and day == day_today:
                format = "%H:%M" # :ss
            localTime = timeday.strftime(format)
        return localTime

    def getTimestamp(self):
        if self.datetime == None:
            return 0.0
        #print("-- {}".format(self._time))
        return float(self.datetime.timestamp())

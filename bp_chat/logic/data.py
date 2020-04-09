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

    def getLogin(self):
        return ''

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

    def is_selected_chat(self):
        return False


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

    @property
    def has_file(self):
        file = self.file
        return file is not None and len(file) > 1


class QuoteInfo:

    message = None
    sender = None
    file = None
    fileName = None
    fileSize = None

    def __init__(self, message, sender, fileName, fileSize, file):
        self.message = message
        self.sender = sender
        sender.quote = self
        self.fileName = fileName
        self.fileSize = fileSize
        self.file = file

    def toHtmlString(self):
        return "<b>" + self.message + "</b>"

    @classmethod
    def make(cls, paramsString, inner):

        #print("......quote: " + paramsString + " inner: " + inner)

        sender_name = cls.excludeParam(paramsString, "sender")
        sender_id = cls.excludeParam(paramsString, "sender_id")
        fileName = cls.excludeParam(paramsString, "file_name")
        fileSize = cls.excludeParam(paramsString, "file_size")
        file = cls.excludeParam(paramsString, "file")

        sz = 0
        if fileSize and len(fileSize) > 0:
            try:
                sz = float(fileSize)
            except Exception as e:
                pass

        return QuoteInfo(inner, QuoteSender(sender_id, sender_name), fileName, sz, file)

    @staticmethod
    def excludeParam(text, paramName):
        param = None
        paramName += "="
        if paramName in text:
            start = text.find(paramName)
            end = text.find(";", start)
            if end < 0:
                end = len(text)
            param = text[start + len(paramName) : end]
        return param

    def getSenderName(self):
        return self.sender.getName()

    def findUserInUsers(self, id):
        self.message.findUserInUsers(id)


class QuoteSender:

    name = None
    id = None
    quote = None

    def __init__(self, sender_id, sender_name):
        self.id = sender_id
        self.name = sender_name

    def getName(self):
        if self.id == None: # FIXME hack for old format...
            self.id = self.name
        if self.id != None:
            sender = self.quote.findUserInUsers(self.id)
            if sender != None:
                return sender.name
        return self.name
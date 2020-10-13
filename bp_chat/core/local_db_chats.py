from bp_chat.core.local_db_core import LocalDbCore


class ChatPoint:

    def __init__(self, chat_id, muted, pinned):
        self.chat_id = chat_id
        self.muted = muted
        self.pinned = pinned


class LocalDbChats(LocalDbCore):

    @classmethod
    def startup(cls, conn):
        print('[ LocalDbChats ]->[ startup ]')
        _ = conn.execute('''CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server VARCHAR(50) NOT NULL,
            chat_id INTEGER NOT NULL,
            muted INTEGER,
            pinned INTEGER
        )''')
        conn.commit()

    @classmethod
    @LocalDbCore.into_db_executor
    def get_chats(cls, server):
        conn = cls.get_instance().conn
        cursor = conn.cursor()
        d = {}
        cursor.execute('SELECT chat_id, muted, pinned FROM chats WHERE server=?', (server,))
        for row in cursor:
            d[row[0]] = ChatPoint(row[0], row[1], row[2])
        return d

    @classmethod
    @LocalDbCore.into_db_executor
    def get_chat(cls, server, chat_id):
        conn = cls.get_instance().conn
        cursor = conn.cursor()
        cursor.execute('SELECT muted, pinned FROM chats WHERE server=? AND chat_id=?', (server, chat_id))
        chat = None
        for row in cursor:
            chat = ChatPoint(chat_id, row[0], row[1])
            break
        if not chat:
            chat = ChatPoint(chat_id, 0, 0)
        return chat

    @classmethod
    @LocalDbCore.into_db_executor
    def add_chat(cls, server, chat_id, muted, pinned):
        conn = cls.get_instance().conn
        cursor = conn.cursor()

        cursor.execute("""SELECT muted, pinned FROM chats WHERE server=? AND chat_id=?""", (server, chat_id))
        chat = None
        for row in cursor:
            chat = ChatPoint(chat_id, row[0], row[1])
            break

        if chat:
            if muted == None:
                muted = chat.muted
            if pinned == None:
                pinned = chat.pinned
            if chat.muted != muted or chat.pinned != pinned:
                _ = cursor.execute("""UPDATE chats SET muted=?, pinned=? WHERE server=? AND chat_id=?""", (muted, pinned, server, chat_id))
                conn.commit()
        else:
            if muted == None:
                muted = 0
            if pinned == None:
                pinned = 0
            print('ADD chat: {}/{} muted:{} pinned:{}'.format(server, chat_id, muted, pinned))
            _ = cursor.execute("""INSERT INTO chats (server, chat_id, muted, pinned) VALUES (?, ?, ?, ?)""", (server, chat_id, muted, pinned))
            conn.commit()
        

LocalDbCore.register(LocalDbChats)


from bp_chat.core.local_db_core import LocalDbCore
from bp_chat.logic.datas.Message import Message

class MessagesMap(LocalDbCore):

    images = {}

    @classmethod
    def startup(cls, conn):
        print('[ MessagesMap ]->[ startup ]')
        _ = conn.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mes_id INTEGER NOT NULL,
            server VARCHAR(50) NOT NULL,
            chat_id INTEGER NOT NULL, 
            sender_id INTEGER NOT NULL, 
            time INTEGER NOT NULL, 
            text text NOT NULL,
            file VARCHAR(50), 
            file_size INTEGER NOT NULL, 
            delivered INTEGER NOT NULL, 
            api_type VARCHAR(50), 
            api_kwargs TEXT
        )''')
        conn.commit()

        cursor = conn.cursor()
        cursor.execute('SELECT name FROM versions')
        _versions = [row[0] for row in cursor]
        if "fix_2" not in _versions:
            print('[ DB-FIX ] fix_2')
            conn.execute('DELETE FROM messages')
            conn.commit()
            cursor.execute("INSERT INTO versions (name) VALUES (?)", ("fix_2",))
            conn.commit()

    @classmethod
    def get_range(cls, server, chat_id, last_message=0, range=20):
        fut = cls.executor().submit(cls._get_range, server, chat_id, last_message, range)
        return fut.result()

    @classmethod
    def _get_range(cls, server, chat_id, last_message, range):
        conn = cls.get_instance().conn
        cursor = conn.cursor()
        lst = []
        if last_message <= 0:
            cursor.execute('SELECT mes_id, chat_id, sender_id, text, time, file, file_size, delivered, api_type, api_kwargs FROM messages WHERE server=? AND chat_id=? ORDER BY ID DESC LIMIT ?',
                           (server, chat_id, range))
        else:
            #                      0       1        2          3     4     5     6          7          8         9
            cursor.execute('SELECT mes_id, chat_id, sender_id, text, time, file, file_size, delivered, api_type, api_kwargs FROM messages WHERE server=? AND chat_id=? AND ID<? ORDER BY ID DESC LIMIT ?',
                           (server, chat_id, last_message, range))
        for row in cursor:
            m = Message(row[3], row[0])
            m.chat_id = row[1]
            m.sender_id = row[2]
            m.timestamp = row[4]
            m.file = row[5]
            m.file_size = row[6]
            m.delivered = row[7]
            m.api_type = row[8]
            m.api_kwargs = row[9]
            lst.append(m)
        return lst[::-1]

    @classmethod
    def insert_message(cls, message, server):
        fut = cls.executor().submit(cls._insert_message, message, server)
        return fut.result()

    @classmethod
    def _insert_message(cls, message, server):
        conn = cls.get_instance().conn
        cursor = conn.cursor()
        m = message
        if not cls._set_message_delivered(m.mes_id, server, m.delivered):
            print('ADD')
            _ = cursor.execute("""INSERT INTO messages 
            (mes_id, server, chat_id, sender_id, time, text, file, file_size, delivered, api_type, api_kwargs) VALUES 
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                               (m.mes_id, server, m.chat_id, m.sender_id, m.timestamp, m._text, m.file, m.file_size,
                                m.delivered, m.api_type, m.api_kwargs))
            conn.commit()

    @classmethod
    def set_message_delivered(cls, mes_id, server, delivered):
        fut = cls.executor().submit(cls._set_message_delivered, mes_id, server, delivered)
        return fut.result()

    @classmethod
    def _set_message_delivered(cls, mes_id, server, delivered):
        conn = cls.get_instance().conn
        cursor = conn.cursor()
        _ = cursor.execute('SELECT delivered FROM messages WHERE server=? AND mes_id=?', (server, mes_id))
        row = cursor.fetchone()
        if not row:
            return False
        if row[0] != delivered:
            _ = cursor.execute("""UPDATE messages SET delivered=? WHERE server=? AND mes_id=?""",
                                (delivered, server, mes_id))
            conn.commit()
        return True
        

LocalDbCore.register(MessagesMap)
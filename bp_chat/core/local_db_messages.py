
from bp_chat.core.local_db_core import LocalDbCore
from bp_chat.logic.datas.Message import Message


class LocalDbMessagesMap(LocalDbCore):

    images = {}

    @classmethod
    def startup(cls, conn):
        print('[ LocalDbMessagesMap ]->[ startup ]')

        with cls.no_version(conn, "fix_messages_5") as no:
            if no:
                conn.execute('DROP TABLE IF EXISTS messages')
                conn.commit()

        _ = conn.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mes_id INTEGER NOT NULL,
            prev_id INTEGER,
            server VARCHAR(50) NOT NULL,
            chat_id INTEGER, 
            sender_id INTEGER, 
            timestamp INTEGER, 
            text_full text,
            file VARCHAR(50), 
            file_size INTEGER, 
            delivered INTEGER,
            api_type VARCHAR(50), 
            api_kwargs TEXT,
            favorite INTEGER,
            got_time INTEGER DEFAULT 0
        )''')
        conn.commit()
    
    @classmethod
    @LocalDbCore.into_db_executor
    def get_range(cls, server, chat_id, last_message=0, range=20):
        conn = cls.get_instance().conn
        cursor = conn.cursor()
        lst = []
        names = 'mes_id, chat_id, sender_id, text_full, timestamp, file, file_size, delivered, api_type, api_kwargs, prev_id, favorite, got_time'
        sql = 'SELECT {names} FROM messages WHERE server=? AND chat_id=? {filt} ORDER BY mes_id DESC LIMIT ?'
        
        if not last_message or last_message < 0:
            filt = ''
            _values = (server, chat_id, range)
        else:
            filt = 'AND ID<?'
            _values = (server, chat_id, last_message, range)

        sql = sql.format(names=names, filt=filt)
        print('[ SQL ] {} :: {}'.format(sql, _values))
        cursor.execute(sql, _values)

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
            m.prev_id = row[10]
            m.favorite = row[11]
            m.got_time = row[12]
            lst.append(m)
        return lst[::-1]

    @classmethod
    def insert_message_got(cls, message, server):
        cls.add_synced('messages', server, 'mes_id', message.mes_id, 
            names=('chat_id', 'sender_id', 'timestamp', 'text_full', 'file', 'file_size', 'delivered', 'api_type', 'api_kwargs', 'prev_id', 'got_time'), 
            obj=message)

    @classmethod
    def set_message_delivered(cls, mes_id, server, delivered):
        cls.add_synced('messages', server, 'mes_id', mes_id, 
            names=('delivered', ), 
            values=(1 if delivered else 0, ))
        
    @classmethod
    def set_message_favorite(cls, server, mes_id, favorite):
        cls.add_synced('messages', server, 'mes_id', mes_id, 
            names=('favorite', ), 
            values=(1 if favorite else 0, ))

    @classmethod
    @LocalDbCore.into_db_executor
    def get_message_favorite(cls, server, mes_id):
        conn = cls.get_instance().conn
        cursor = conn.cursor()
        cursor.execute('SELECT favorite FROM messages WHERE server=? AND mes_id=?', (server, mes_id))
        row = cursor.fetchone()
        return row[0] if row else 0

LocalDbCore.register(LocalDbMessagesMap)
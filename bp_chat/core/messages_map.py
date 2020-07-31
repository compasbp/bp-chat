
from bp_chat.core.local_db_core import LocalDbCore


class MessagesMap(LocalDbCore):

    images = {}

    @classmethod
    def startup(cls, conn):
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
        # mes_id, server, chat_id, sender_id, time, text, file, file_size, delivered, api_type, api_kwargs

    @classmethod
    def get_range(cls, chat_id, last_message=0, range=100):
        fut = cls.executor().submit(cls._get_range, chat_id, last_message, range)
        return fut.result()

    @classmethod
    def _get_range(cls, chat_id, last_message, range):
        conn = cls.get_instance().conn
        cursor = conn.cursor()
        if last_message <= 0:
            _ = cursor.execute('SELECT * FROM messages WHERE chat_id=?', (chat_id,))
        row = cursor.fetchone()
        if row:
            filename = row[3]
        elif filename:
            _ = cursor.execute('SELECT count(id) FROM files WHERE name=?', (filename,))
            row = cursor.fetchone()
            num = row[0] + 1
            if '.' in filename:
                lst = filename.split(".")
                pre, sub = '.'.join(lst[:-1]), lst[-1]
                new_filename = '{}_bp{}.{}'.format(pre, num, sub)
            else:
                new_filename = '{}_bp{}'.format(filename, num)
            cursor.execute("INSERT INTO files (name, uuid, filename) VALUES (?, ?, ?)", (filename, file_uuid, new_filename))
            conn.commit()
            filename = new_filename

        return filename

    @classmethod
    def insert_message(cls, message, server):
        pass

    @classmethod
    def _insert_message(cls, message, server):
        conn = cls.get_instance().conn
        cursor = conn.cursor()
        m = message
        #     text = ""
        #     sender_id = None
        #     mes_id = None
        #     chat_id = None
        #
        #     quote:QuoteInfo = None
        #     file = None
        #     file_size = None
        #
        #     _time = None
        #     is_html = False
        #     has_links = False
        #     _links = []
        #     _delivered = True # delivered?
        #
        #     api_type = None
        #     api_kwargs = None
        #
        #     _selected_text = None

        _ = cursor.execute("""INSERT INTO messages 
        (mes_id, server, chat_id, sender_id, time, text, file, file_size, delivered, api_type, api_kwargs) VALUES 
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                           (m.mes_id, server, m.chat_id, m.sender_id, m.time, m.text, m.file, m.file_size,
                            m.delivered, m.api_type, m.api_kwargs))

LocalDbCore.register(MessagesMap)
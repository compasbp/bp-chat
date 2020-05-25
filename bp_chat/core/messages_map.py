
from bp_chat.core.local_db_core import LocalDbCore


class MessagesMap(LocalDbCore):

    images = {}

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
    def insert_message(cls, message):
        pass
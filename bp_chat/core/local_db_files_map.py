
from os.path import join, expanduser

from bp_chat.core.app_common import get_app_dir_path, with_uid_suf, APP_NAME_DIR
from bp_chat.core.local_db_core import LocalDbCore


def getDownloadsFilePath(filename, file_uuid):
    _filename = LocalDbFilesMap.get(filename, file_uuid)
    return join(getDownloadsDirectoryPath(), APP_NAME_DIR, _filename)

def getDownloadsDirectoryPath():
    return join(expanduser('~'), 'Downloads')

def get_files_db_path():
    return join(get_app_dir_path(), with_uid_suf('.chat'), 'files.db')


class LocalDbFilesMap(LocalDbCore):

    images = {}

    @classmethod
    def startup(cls, conn):
        print('[ LocalDbFilesMap ]->[ startup ]')

        with cls.no_version(conn, "fix_1") as no:
            if no:
                print('[ DB-FIX ] fix_1')
                conn.execute('DROP TABLE IF EXISTS files')
                conn.commit()
                # cursor.execute("INSERT INTO versions (name) VALUES (?)", ("fix_1",))
                # conn.commit()

        _ = conn.execute('''CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name text NOT NULL,
                uuid text NOT NULL UNIQUE,
                filename text NOT NULL UNIQUE )''')
        conn.commit()

    @classmethod
    def get(cls, filename, file_uuid):
        fut = cls.executor().submit(cls._get, filename, file_uuid)
        return fut.result()

    @classmethod
    def _get(cls, filename, file_uuid):
        conn = cls.get_instance().conn
        cursor = conn.cursor()
        _ = cursor.execute('SELECT * FROM files WHERE uuid=?', (file_uuid,))
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

LocalDbCore.register(LocalDbFilesMap)

from os.path import join, expanduser
import sqlite3
from concurrent.futures import ThreadPoolExecutor

from bp_chat.core.app_common import get_app_dir_path, with_uid_suf, APP_NAME_DIR


def getDownloadsFilePath(filename, file_uuid):
    _filename = FilesMap.get(filename, file_uuid)
    return join(getDownloadsDirectoryPath(), APP_NAME_DIR, _filename)

def getDownloadsDirectoryPath():
    return join(expanduser('~'), 'Downloads')


def get_files_db_path():
    return join(get_app_dir_path(), with_uid_suf('.chat'), 'files.db')


class FilesMap:

    _instance = None
    __executor = None
    images = {}

    @classmethod
    def executor(cls):
        if not cls.__executor:
            cls.__executor = ThreadPoolExecutor(max_workers=1)
        return cls.__executor

    def __init__(self):
        db_path = get_files_db_path()
        self.conn = sqlite3.connect(db_path)
        ret = self.conn.execute('''CREATE TABLE IF NOT EXISTS versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name text NOT NULL )''')
        self.conn.commit()

        cursor = self.conn.cursor()
        cursor.execute('SELECT name FROM versions')
        _versions = [row[0] for row in cursor]
        if "fix_1" not in _versions:
            print('[ DB-FIX ] fix_1')
            self.conn.execute('DROP TABLE IF EXISTS files')
            self.conn.commit()
            cursor.execute("INSERT INTO versions (name) VALUES (?)", ("fix_1",))
            self.conn.commit()

        ret = self.conn.execute('''CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name text NOT NULL,
            uuid text NOT NULL UNIQUE,
            filename text NOT NULL UNIQUE )''')
        self.conn.commit()

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = FilesMap()
        return cls._instance

    @classmethod
    def get(cls, filename, file_uuid):
        fut = cls.executor().submit(cls._get, filename, file_uuid)
        return fut.result()

    @classmethod
    def _get(cls, filename, file_uuid):
        conn = cls.get_instance().conn
        cursor = conn.cursor()
        ret = cursor.execute('SELECT * FROM files WHERE uuid=?', (file_uuid,))
        row = cursor.fetchone()
        if row:
            filename = row[3]
        else:
            ret = cursor.execute('SELECT count(id) FROM files WHERE name=?', (filename,))
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

        #print('[ FILE ] {}'.format(filename))
        return filename
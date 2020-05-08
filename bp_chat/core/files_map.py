
from os.path import join, expanduser
import sqlite3
from concurrent.futures import ThreadPoolExecutor

from bp_chat.core.app_common import get_app_dir_path, with_uid_suf, APP_NAME_DIR
from bp_chat.core.local_db_core import LocalDbCore


def getDownloadsFilePath(filename, file_uuid):
    _filename = FilesMap.get(filename, file_uuid)
    return join(getDownloadsDirectoryPath(), APP_NAME_DIR, _filename)

def getDownloadsDirectoryPath():
    return join(expanduser('~'), 'Downloads')

def get_files_db_path():
    return join(get_app_dir_path(), with_uid_suf('.chat'), 'files.db')


class FilesMap(LocalDbCore):

    images = {}

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
        elif filename:
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

        return filename

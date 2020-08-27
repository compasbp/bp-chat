from os.path import join
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

from bp_chat.core.app_common import get_app_dir_path, with_uid_suf, APP_NAME_DIR
from .tryable import tryable


def get_files_db_path():
    return join(get_app_dir_path(), with_uid_suf('.chat'), 'files.db')


class LocalDbCore:

    _instance = None
    __executor = None
    _registered = []

    @classmethod
    def executor(cls):
        if not cls.__executor:
            cls.__executor = ThreadPoolExecutor(max_workers=1)
        return cls.__executor

    @classmethod
    def register(cls, reg_cls):
        if reg_cls not in LocalDbCore._registered:
            LocalDbCore._registered.append(reg_cls)

    @classmethod
    def startup(cls, conn):
        print('[ LocalDbCore ]->[ startup ]')
        _ = conn.execute('''CREATE TABLE IF NOT EXISTS versions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name text NOT NULL )''')
        conn.commit()

    def __init__(self):
        db_path = get_files_db_path()
        self.conn = sqlite3.connect(db_path)
        for reg in LocalDbCore._registered:
            reg.startup(self.conn)

    @classmethod
    def get_instance(cls):
        if not LocalDbCore._instance:
            LocalDbCore._instance = LocalDbCore()
        return LocalDbCore._instance

    @classmethod
    @contextmanager
    def no_version(cls, conn, ver):
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM versions')
        _versions = [row[0] for row in cursor]
        need = ver not in _versions
        yield need
        if need:
            cursor.execute("INSERT INTO versions (name) VALUES (?)", (ver,))
            conn.commit()

    @classmethod
    def into_db_executor(cls, func):
    
        def new_func(*args, **kwargs):
            fut = cls.executor().submit(func, *args, **kwargs)
            return fut.result()

        return new_func
        

LocalDbCore.register(LocalDbCore)

from os.path import join, dirname, exists
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

from bp_chat.core.app_common import get_app_dir_path, with_uid_suf, APP_NAME_DIR
from .tryable import tryable


def get_files_db_path():
    return join(get_app_dir_path(), with_uid_suf('.chat'), 'files.db')


class _LocalDbCoreBase:

    __executor = None

    @classmethod
    def executor(cls):
        if not _LocalDbCoreBase.__executor:
            _LocalDbCoreBase.__executor = ThreadPoolExecutor(max_workers=1)
        return _LocalDbCoreBase.__executor

    @classmethod
    def into_db_executor(cls, func):
    
        def new_func(*args, **kwargs):
            fut = cls.executor().submit(func, *args, **kwargs)
            return fut.result()

        return new_func


class LocalDbCore(_LocalDbCoreBase):

    _instance = None
    _registered = []

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
        _dir = dirname(db_path)
        if not exists(_dir):
            os.makedirs(_dir)
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
        if need:
            print('[ DB-FIX ] {}'.format(ver))
        yield need
        if need:
            cursor.execute("INSERT INTO versions (name) VALUES (?)", (ver,))
            conn.commit()

    @classmethod
    @_LocalDbCoreBase.into_db_executor
    def add_synced(cls, table, server, id_name, id_value, names, obj=None, values=None):
        conn = cls.get_instance().conn
        cursor = conn.cursor()
        filt = 'server=? AND {id_name}=?'.format(id_name=id_name)

        _ = cursor.execute('SELECT {names} FROM {table} WHERE {filt}'.format(
            table = table,
            filt = filt,
            names = ', '.join(names)
        ), (server, id_value))
        row = cursor.fetchone()
        if row:
            changed = False
            ch_names, ch_values = [], []
            for i, a in enumerate(names):
                vl = getattr(obj, a) if obj else values[i]
                if vl != row[i]:
                    changed = True
                    ch_names.append(a)
                    ch_values.append(vl)

            if changed:
                _args = ch_values + [server, id_value]
                _ = cursor.execute(
                    'UPDATE {table} SET {sets} WHERE {filt}'.format(
                        table = table,
                        sets = ', '.join([n+'=?' for n in ch_names]),
                        filt = filt
                    ), _args)
                conn.commit()
        else:
            #print('ADD')
            _names = ['server', id_name] + list(names)
            _values = [server, id_value] + [getattr(obj, a) if obj else values[i] for i, a in enumerate(names)]
            _ = cursor.execute("""INSERT INTO messages ({names}) VALUES ({values})""".format(
                names = ', '.join(_names),
                values = ', '.join(['?' for _ in _names])
            ), _values)
            conn.commit()
        

LocalDbCore.register(LocalDbCore)

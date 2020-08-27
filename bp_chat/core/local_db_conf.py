from bp_chat.core.local_db_core import LocalDbCore


class ConfPoint:

    def __init__(self, category, name, value):
        self.category = category
        self.name = name
        self.value = value


class LocalDbConf(LocalDbCore):

    @classmethod
    def startup(cls, conn):
        print('[ LocalDbConf ]->[ startup ]')
        _ = conn.execute('''CREATE TABLE IF NOT EXISTS conf (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server VARCHAR(50),
            category VARCHAR(50),
            name VARCHAR(50),
            value VARCHAR(150)
        )''')
        conn.commit()

    # @classmethod
    # def get_conf(cls, server):
    #     fut = cls.executor().submit(cls._get_conf, server)
    #     return fut.result()

    @classmethod
    @LocalDbCore.into_db_executor
    def get_conf(cls, server):
        conn = cls.get_instance().conn
        cursor = conn.cursor()
        d = {}
        cursor.execute('SELECT category, name, value FROM conf WHERE server=?', (server,))
        for row in cursor:
            category = d.get(row[0], None)
            if not category:
                category = {}
                d[row[0]] = category
            category[row[1]] = row[2]
        return d

    # @classmethod
    # def set_conf_value(cls, server, category, name, value):
    #     fut = cls.executor().submit(cls._set_conf_value, server, category, name, value)
    #     return fut.result()

    @classmethod
    @LocalDbCore.into_db_executor
    def set_conf_value(cls, server, category, name, value):
        conn = cls.get_instance().conn
        cursor = conn.cursor()

        cursor.execute("""SELECT value FROM conf WHERE server=? AND category=? AND name=?""", (server, category, name))
        m = None
        for row in cursor:
            m = ConfPoint(category, name, row[0])
            break

        if m:
            if m.value != value:
                _ = cursor.execute("""UPDATE conf SET value=? WHERE server=? AND category=? AND name=?""", (value, server, category, name))
                conn.commit()
        else:
            print('ADD: {}/{}.{} = {}'.format(server, category, name, value))
            _ = cursor.execute("""INSERT INTO conf (server, category, name, value) VALUES (?, ?, ?, ?)""", (server, category, name, value))
            conn.commit()
        

LocalDbCore.register(LocalDbConf)

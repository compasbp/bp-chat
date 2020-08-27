from os.path import exists, dirname, join, expanduser
import sys, os
from copy import deepcopy
from configparser import ConfigParser

if __name__=='__main__':
    import sys, os
    sys.path.insert(0, os.path.abspath('.'))

from bp_chat.core.app_common import with_uid_suf
from bp_chat.core.app_common import get_app_dir_path
from bp_chat.core.local_db_conf import LocalDbConf
from bp_chat.core.local_db_chats import LocalDbChats


class SimpleConfig:

    _config = None
    app_name = None
    conf_name = None
    structure = None
    _data = None
    server_uid = ''

    def __init__(self,conf_name, structure=None):
        self.conf_name = conf_name
        self.structure = structure

    def set_value(self, title, name, value):
        self._data[title][name] = value

    def get_value(self, title, name):
        return self._data[title][name]

    def __setattr__(self, key, value):
        if hasattr(self, key):
            super().__setattr__(key, value)

    def __getitem__(self, item):
        return self._data[item]

    def load(self):
        print('[ LOAD ] si: {}'.format(self.server_uid))
        self._data = LocalDbConf.get_conf(self.server_uid)
        self._config = ConfigParser(allow_no_value=True)
        # for title, d in self.structure.items():
        #     d = self._fix_dict(d)
        #     self._config[title] = d
        #     self._data[title] = deepcopy(d)

        path = self.get_conf_path()
        if exists(path):
            text = open(path).read()
            self._config.read_string(text)

        for title, d in self.structure.items():
            #print('...!!! {} {}'.format(title, type(d)))
            if type(d) == dict:
                try:
                    c_d = self._config[title]
                except:
                    c_d = {}
                d_d = self._data.get(title, None)
                # if d_d == None:
                #     self._data[title] = d_d = deepcopy(self._fix_dict(d))
                # cat = self._config_in_db.get(title, None)
                # if cat == None:
                #     self._config_in_db = cat = {}
                for name, value in d.items():
                    #print('...val: {}'.format(value))
                    #print('..{} -> {} = {}'.format(name, type(value), hasattr(value, 'to_value')))
                    if hasattr(value, 'to_value'):
                        tp = value.to_value
                    else:
                        tp = type(value)
                    #vl = tp(c_d[name])
                    #d_d[name] = vl
                    if d_d != None and name in d_d:
                        #print('...>> 1')
                        d_d[name] = tp(d_d[name])
                    else:
                        if d_d == None:
                            self._data[title] = d_d = {}
                        if name in c_d:
                            #print('...>> 2')
                            d_d[name] = tp(c_d[name])
                        else:
                            vl = tp(d[name])
                            #print('...!!! >> {} -> {}'.format(name, vl))
                            d_d[name] = vl
                        # else:
                        #     d_d[name] = tp(c_d[name])

        #print(self._data)
    
    def _fix_dict(self, d):
        if type(d) == dict:
            d = deepcopy(d)
            for name, value in d.items():
                if hasattr(value, 'conf_type'):
                    tp = value.conf_type
                else:
                    tp = type(value)
                d[name] = tp(d[name])
        return d

    def save(self):
        print('[ SAVE ] si: {}'.format(self.server_uid))
        path = self.get_conf_path()
        print('  ... {}'.format(path))
        dir_path = dirname(path)
        if not exists(dir_path):
            os.makedirs(dir_path)

        #print(self._data)

        for title, d in self.structure.items():
            if type(d) == dict:
                #c_d = self._config[title]
                d_d = self._data[title]
                for name, value in d.items():
                    if hasattr(value, 'from_value'):
                        value = value.from_value(d_d[name])
                    else:
                        value = str(d_d[name])
                    #c_d[name] = value

                    LocalDbConf.set_conf_value(self.server_uid, title, name, value)

        # with open(path, 'w') as configfile:
        #     self._config.write(configfile)

        if exists(path):
            os.remove(path)

    def get_conf_path(self):
        return join(get_app_dir_path(), self.conf_name)



class _AppConfig(SimpleConfig):

    def __init__(self, conf_name=None, structure=None):
        super().__init__(conf_name=conf_name, structure=structure)

    def __getattr__(self, item):
        #print(f'[ GET ] {item}')
        for a in self.structure:
            if item == a:
                return self._data[a]

            elif item.startswith(a + "_"):
                it = self._data[a]
                st = self.structure[a]
                for b in it:
                    if a + "_" + b == item:
                        #print('\t-> {} . {}'.format(a, b))
                        st_b = st[b]
                        if hasattr(st_b, 'to_value'):
                            return st_b.to_value(it[b])
                        else:
                            return it[b]

    def __setattr__(self, item, value):
        if not self.structure or item.startswith('_'):
            return super().__setattr__(item, value)

        for a in self.structure:
            if item == a:
                #return self.structure[a]
                print('{} -> {}'.format(self._data[a], value))

            elif item.startswith(a + "_"):
                it = self._data[a]
                st = self.structure[a]
                for b in it:
                    if a + "_" + b == item:
                        st_b = st[b]
                        #print('{} -> {}'.format(it[b], value))
                        # if hasattr(st_b, 'from_value'):
                        #     it[b] = st_b.from_value(value)
                        # else:
                        it[b] = value


class BaseValue:

    def __str__(self):
        return self.from_value()

    def __repr__(self):
        return self.__str__()

    def from_value(self):
        pass


class IntValue(BaseValue):

    conf_type = str

    def __init__(self, default):
        self.default = int(default)

    def to_value(self, val):
        try:
            value = int(val)
        except:
            value = self.default
        return value

    def from_value(self, value=None):
        if value == None:
            value = self.default
        return str(value)


class BoolValue(BaseValue):

    conf_type = str

    def __init__(self, default):
        self.default = self._to_value(default)

    def _to_value(self, value):
        return True if value in (True, 1, 'True', '1', 'TRUE') else False

    def to_value(self, val):
        try:
            value = self._to_value(val)
        except:
            value = self.default
        return value

    def from_value(self, value=None):
        if value == None:
            value = self.default
        return '1' if value else '0'


class AppConfig(_AppConfig):

    def __init__(self, conf_name=with_uid_suf(".chat")+"/messages.conf"):
        super().__init__(conf_name=conf_name, structure={'server':{
            'server': '0',
            'server2': '0',
            'useServer2': BoolValue('0'),
            'started': BoolValue('0'),
            'user_name_start': ''
        }, 'window':{
            'width': IntValue('1000'),
            'height': IntValue('600'),
            'main_split_w': IntValue('330'),
            'main_split_h': IntValue('670'),
            'maximized': BoolValue('0'),
            'x': IntValue('-1'),
            'y': IntValue('-1'),
            'fontSize':IntValue('-1'),
        }, 'user':{
            'lang': 'ru'
        }})


class ConnectConfig(_AppConfig):

    def __init__(self, server_uid):
        self.server_uid = server_uid
        conf_name = with_uid_suf(".chat") + "/srvs/" + server_uid
        super().__init__(conf_name=conf_name, structure={
            'user': {
                'mutes': '',                # chats
                'last_reads': '',           # chats
                'favorites_messages': '',   # messages
                'pinned_chats': ''          # chats
            },
            'auth': {
                'utkn': ''
            }
        })

    def load(self):
        super().load()
        pinned = self.user_pinned_chats.split(',')
        pinned = [int(p) for p in pinned if p]
        print('[pinned] {}'.format(pinned))
        for chat_id in pinned:
            self.set_pinned_chat(chat_id, 1)

        mutes = self.user_mutes
        mutes = [m for m in (a.strip() for a in mutes.split(',')) if len(m) > 0] if mutes else []
        print('[mutes] {}'.format(mutes))
        for chat_id in mutes:
            self.set_muted_chat(chat_id, 1)

        self.user_mutes = ''
        self.user_last_reads = ''
        self.user_favorites_messages = ''
        self.user_pinned_chats = ''

    def get_utkn(self):
        return self.auth_utkn

    def set_utkn(self, utkn):
        self.auth_utkn = utkn

    def get_pinned_chats(self):
        pinned = set()
        chats = LocalDbChats.get_chats(self.server_uid)
        for _, c in chats.items():
            if c.pinned:
                pinned.add(c.chat_id)
        return list(pinned)

    def get_pinned_chat(self, chat_id):
        chat = LocalDbChats.get_chat(self.server_uid, chat_id)
        pinned = chat.pinned
        return pinned

    def set_pinned_chat(self, chat_id, pinned):
        LocalDbChats.add_chat(self.server_uid, chat_id, muted=None, pinned=pinned)

    def get_muted_chat(self, chat_id):
        chat = LocalDbChats.get_chat(self.server_uid, chat_id)
        muted = chat.muted
        return muted

    def set_muted_chat(self, chat_id, muted):
        LocalDbChats.add_chat(self.server_uid, chat_id, muted=muted, pinned=None)



if __name__=='__main__':

    conf = _AppConfig(
        conf_name = ".chat" + "/messages.conf",
        structure = {
            'server': {
                'server': '0',
                'local_server': '0',
                'useServer2': '0',
                'started': '0',
                'user_name_start': ''
            },
            'window': {
                'width': '1000',
                'height': '600',
                'main_split_w': '330',
                'main_split_h': '670',
                'maximized': '0',
                'x': '-1',
                'y': '-1',
            }
        }
    )
    conf.load()

    print(conf.server_server)
    print(conf.window_width)
    print(conf.server)

    conf.window_main_split_h = '680'
from os.path import exists, dirname, join, expanduser
import sys, os
from copy import deepcopy
from configparser import ConfigParser

if __name__=='__main__':
    import sys, os
    sys.path.insert(0, os.path.abspath('.'))

from bp_chat.core.app_common import with_uid_suf
from bp_chat.core.app_common import get_app_dir_path


class SimpleConfig:

    _config = None
    app_name = None
    conf_name = None
    structure = None
    _data = None

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
        print('[ LOAD ]')
        self._data = {}
        self._config = ConfigParser(allow_no_value=True)
        for title, d in self.structure.items():
            d = self._fix_dict(d)
            self._config[title] = d
            self._data[title] = deepcopy(d)

        path = self.get_conf_path()
        if exists(path):
            text = open(path).read()
            self._config.read_string(text)

        for title, d in self.structure.items():
            if type(d) == dict:
                c_d = self._config[title]
                d_d = self._data[title]
                for name, value in d.items():
                    #print('..{} -> {} = {}'.format(name, type(value), hasattr(value, 'to_value')))
                    if hasattr(value, 'to_value'):
                        tp = value.to_value
                    else:
                        tp = type(value)
                    d_d[name] = tp(c_d[name])

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
        print('[ SAVE ]')
        path = self.get_conf_path()
        dir_path = dirname(path)
        if not exists(dir_path):
            os.makedirs(dir_path)

        #print(self._data)

        for title, d in self.structure.items():
            if type(d) == dict:
                c_d = self._config[title]
                d_d = self._data[title]
                for name, value in d.items():
                    if hasattr(value, 'from_value'):
                        value = value.from_value(d_d[name])
                    else:
                        value = str(d_d[name])
                    c_d[name] = value

        with open(path, 'w') as configfile:
            self._config.write(configfile)

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
        }, 'user':{
            'lang': 'ru'
        }})


class ConnectConfig(_AppConfig):

    def __init__(self, server_uid):
        conf_name = with_uid_suf(".chat") + "/srvs/" + server_uid
        super().__init__(conf_name=conf_name, structure={'user': {
            'mutes': '',
            'last_reads': '',
            'favorites_messages': '',
            'pinned_chats': ''
        }})

    def get_last_reads(self):
        lasts = self.user_last_reads.split(',')
        lasts = [la.split(':') for la in lasts if la]
        return {la[0]:la[1] for la in lasts if len(la) > 0}

    def set_last_reads(self, lasts):
        print(f'....... lasts:\n{lasts}\n<<<<<<<<<\n')
        self.user_last_reads = ','.join('{}:{}'.format(key, val) for key, val in lasts.items())
        print(f'>>>>>>> user_last_reads:\n{self.user_last_reads}\n<<<<<<<<<\n')

    def get_pinned_chats(self):
        pinned = self.user_pinned_chats.split(',')
        return [int(p) for p in pinned if p]

    def set_pinned_chats(self, pinned):
        self.user_pinned_chats = ','.join([str(p) for p in pinned])



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
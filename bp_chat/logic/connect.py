from requests import get, exceptions
from json import JSONDecodeError

from bp_chat.core.action import Action, ActionGroup, ActionsQueue


class Connection:

    _on_connected = None

    def __init__(self, addresses, app):
        self.app = app
        self.points = [ServerPoint(a, self) for a in addresses]

    def connect(self):
        self._do_in_actions_queue('connect')

    def disconnect(self):
        self._do_in_actions_queue('disconnect')

    def _do_in_actions_queue(self, method):
        queue = ActionsQueue.instance()
        actions = [Action.by_target(getattr(p, method))
                   for p in self.points]
        queue.append(ActionGroup(*actions))

    @property
    def on_connected(self):
        return self._on_connected

    @on_connected.setter
    def on_connected(self, val):
        self._on_connected = val


class ServerPoint:

    address: str

    def __init__(self, address: str, connection: Connection):
        pre = 'https'
        port = '8887'

        if '://' in address:
            lst = address.split('://')
            pre, address = lst[0], lst[1]

        if '/' in address:
            address = address.split('/')[0] # FIXME !!!

        if ':' in address:
            lst = address.split(':')
            port, address = lst[1], lst[0]

        self.address = pre + '://' + address + ':' + port + '/api/connect/'
        self.connection = connection

    def connect(self):
        try:
            r = get(self.address, timeout=3, verify=False) # FIXME !!!
        except exceptions.ConnectionError as e:
            self.connection.app.console.debug('cant connect: {}'.format(e))
            return

        try:
            result = r.json()
        except JSONDecodeError as e:
            result = None
            self.connection.app.console.debug(repr(e))

        if result:
            self.on_connected(result)

    def disconnect(self):
        pass

    def on_connected(self, result):
        if self.connection.on_connected:
            self.connection.on_connected(self)
        else:
            self.connection.app.console.debug(result)

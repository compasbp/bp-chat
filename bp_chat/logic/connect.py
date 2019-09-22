from requests import get

from bp_chat.core.action import Action, ActionGroup, ActionsQueue


class Connection:

    _on_connected = None

    def __init__(self, addresses):
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
        self.address = address
        self.connection = connection

    def connect(self):
        self.r = get(self.address, timeout=3)
        self.on_connected()

    def disconnect(self):
        pass

    def on_connected(self):
        self.connection.on_connected(self)

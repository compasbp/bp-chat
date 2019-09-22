


class Connection:

    def __init__(self, addresses):
        self.points = [ServerPoint(a, self) for a in addresses]

    def connect(self):
        for p in self.points:
            p.connect()

    def disconnect(self):
        for p in self.points:
            p.disconnect()


class ServerPoint:

    address: str

    def __init__(self, address: str, connection: Connection):
        self.address = address

    def connect(self):
        pass

    def disconnect(self):
        pass

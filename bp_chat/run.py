from sys import argv

from PyQt5.QtWidgets import QPushButton, QApplication

from bp_chat.core.tryable import tryable
from bp_chat.core.app import as_app
from bp_chat.logic.connect import Connection
from bp_chat.gui.core.gui_thread import to_gui_thread


@as_app
def main():
    if 'api' in argv:
        main_api()
    else:
        main_gui()


def main_api():
    #raise Exception('api')
    from requests import get
    r = get('ya.ru')
    print(len(r.text))


def main_gui():

    #raise Exception(1)
    app = QApplication([])
    w = QPushButton('Connect')
    connection = Connection(['http://ya.ru', 'http://google.com'])

    @tryable
    def tst(*args):
        #raise Exception('njjhj')
        connection.connect()

    @to_gui_thread
    @tryable
    def on_connected(server_point):
        print(f'{server_point.address}: {len(server_point.r.text)}')
        w.setText('Connected')

    connection.on_connected = on_connected

    w.clicked.connect(tst)

    w.show()
    app.exec_()

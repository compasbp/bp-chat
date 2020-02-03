from sys import argv
from time import sleep

from PyQt5.QtWidgets import QPushButton, QApplication

from bp_chat.core.tryable import tryable
from bp_chat.core.app import as_app
from bp_chat.logic.connect import Connection
from bp_chat.gui.core.gui_thread import to_gui_thread


@as_app
def main(app):
    if 'api' in argv:
        main_api(app)
    else:
        main_gui(app)


def main_api(app):
    #raise Exception('api')
    # from requests import get
    # r = get('ya.ru')
    # print(len(r.text))
    con = Connection(['127.0.0.1'], app)
    #con = Connection(['223.1.1.84'], app)
    con.connect()

    while True:
        sleep(1)


def main_gui(app):
    from bp_chat.gui.main import main as _main
    _main()

    # #raise Exception(1)
    # app = QApplication([])
    # w = QPushButton('Connect')
    # connection = Connection(['http://ya.ru', 'http://google.com'])
    #
    # @tryable
    # def tst(*args):
    #     #raise Exception('njjhj')
    #     connection.connect()
    #
    # @to_gui_thread
    # @tryable
    # def on_connected(server_point):
    #     print(f'{server_point.address}: {len(server_point.r.text)}')
    #     w.setText('Connected')
    #
    # connection.on_connected = on_connected
    #
    # w.clicked.connect(tst)
    #
    # w.show()
    # app.exec_()

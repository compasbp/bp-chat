from sys import argv

from PyQt5.QtWidgets import QPushButton, QApplication

from bp_chat.logic.common.tryable import tryable
from bp_chat.logic.common.app import as_app


@as_app
def main():
    if 'api' in argv:
        main_api()
    else:
        main_gui()


def main_api():
    raise Exception('api')


def main_gui():

    #raise Exception(1)
    app = QApplication([])
    w = QPushButton('hello')

    @tryable
    def tst(*args):
        raise Exception('njjhj')

    w.clicked.connect(tst)

    w.show()
    app.exec_()

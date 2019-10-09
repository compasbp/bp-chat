from PyQt5.QtGui import QFontMetrics
from PyQt5.QtCore import Qt

WORD_TYPE_SIMPLE = 0


class MessageDrawer:

    def __init__(self, message, font, text):
        self.message = message
        self._font = font
        message.drawer = self

        self.metrics = QFontMetrics(font)
        w_rect = self.metrics.boundingRect(0, 0, 9999, 9999, Qt.Horizontal, 'w')
        self.line_height = w_rect.height()
        self.w_width = w_rect.width()

        lines = text.split('\n')
        self.lines = [
            [WordDrawer(w, self) for w in line.split(' ')] for line in lines
        ]

    @property
    def font(self):
        return self._font


class WordDrawer(str):

    @staticmethod
    def __new__(cls, word: str, message_drawer: MessageDrawer, word_type: int = WORD_TYPE_SIMPLE):
        obj = str.__new__(cls, word)
        obj.message_drawer = message_drawer
        obj.word_type = word_type
        obj.width = message_drawer.metrics.boundingRect(0, 0, 9999, 9999, Qt.Horizontal, obj).width()
        return obj

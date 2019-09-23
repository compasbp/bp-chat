
from PyQt5.QtWidgets import (QDialog, QApplication, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLayout, QGridLayout, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import QPropertyAnimation, QAbstractAnimation, QRect, QParallelAnimationGroup, Qt, QPoint
from PyQt5.QtGui import QColor, QLinearGradient, QPainter, QBrush


def fix_window(window):
    flags = window.windowFlags()
    flags = int(flags)
    flags &= ~Qt.WindowContextHelpButtonHint
    flags = Qt.WindowFlags(flags)
    window.setWindowFlags(flags)
    return window

def set_widget_background(widget, color):
    if type(color) == str:
        color = QColor(color)
    palette = widget.palette()
    palette.setColor(widget.backgroundRole(), color)
    widget.setPalette(palette)
    widget.setAutoFillBackground(True)
    return palette


class AnimatedDialog(QDialog):

    def showEvent(self, event):
        super().showEvent(event)

        duration = 300

        parent = self.parentWidget()
        if parent:
            pos = parent.pos()
            size = parent.size()
            center = (pos.x() + size.width()/2, pos.y() + size.height()/2)
            parent.setWindowOpacity(0.5)
        else:
            desktop = QApplication.desktop()
            if desktop:
                rect = QApplication.desktop().screenGeometry()
                center = (rect.width()/2, rect.height()/2)
            else:
                center = (100, 100)

        anim1 = QPropertyAnimation(self, b"windowOpacity")
        anim1.setStartValue(0.0)
        anim1.setEndValue(1.0)
        anim1.setDuration(duration)

        w, h = self.width(), self.height()
        w2, h2 = w * 2, h * 2

        anim2 = QPropertyAnimation(self, b"geometry")
        anim2.setDuration(duration)
        anim2.setKeyValueAt(0, QRect(center[0]-w/2, center[1]-h/2, w, h))
        #anim2.setKeyValueAt(0.8, QRect(250, 250, 100, 30))
        anim2.setKeyValueAt(1, QRect(center[0]-w2/2, center[1]-h2/2, w2, h2))

        self.group = QParallelAnimationGroup(self)
        self.group.addAnimation(anim1)
        self.group.addAnimation(anim2)

        self.group.start(QAbstractAnimation.DeleteWhenStopped)

    def hideEvent(self, event):
        super().hideEvent(event)

        parent = self.parentWidget()
        if parent:
            parent.setWindowOpacity(1)


class Toolbar(QWidget):

    LEFT = 'left'
    RIGHT = 'right'
    CENTER = 'center'

    POSES = {
        LEFT: 0, CENTER: 1, RIGHT: 2
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        set_widget_background(self, '#ffc107')

        h = 60

        self.setMaximumHeight(h)
        self.setMinimumHeight(h)

        lay = QGridLayout(self)

        # self.right_lay.setSizeConstraint(QLayout.SetMinimumSize)
        #
        # lay.addLayout(self.left_lay)
        # lay.addLayout(self.center_lay)
        # lay.addLayout(self.right_lay)
        lay.setColumnStretch(1, 100)

        self.left_widget = None
        self.center_widget = None
        self.right_widget = None

    def set_widget(self, widget, to):
        lay = self.layout() #getattr(self, to + '_lay')
        last_widget = getattr(self, to + '_widget')

        if last_widget:
            lay.removeWidget(last_widget)

        setattr(self, to + '_widget', widget)

        lay.addWidget(widget, 0, self.POSES[to])

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)

        h = 1

        start_color = QColor('#777777')
        # start_color.setAlphaF(1.0)
        #
        # # end_color = QColor('#777777')
        # # end_color.setAlphaF(0.0)
        # end_color = self.parentWidget().palette().color(self.parentWidget().backgroundRole())
        #
        # gradient = QLinearGradient()
        # gradient.setColorAt(0.0, start_color)
        # gradient.setColorAt(1.0, end_color)
        # gradient.setStart(QPoint(0, self.height()-h))
        # gradient.setFinalStop(QPoint(0, self.height()))

        brush = QBrush(start_color)
        painter.setBrush(brush)
        painter.drawRect(QRect(QPoint(0, self.height()-h), QPoint(self.width(), self.height())))


class ImagedButton(QWidget):

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)


if __name__=='__main__':

    app = QApplication([])

    w = fix_window(QWidget())
    w.resize(800, 800)
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)

    toolbar = Toolbar(w)
    lay.addWidget(toolbar)

    button = fix_window(QPushButton("Test", w))
    toolbar.set_widget(button, Toolbar.RIGHT)
    toolbar.set_widget(QLabel('Test'), Toolbar.CENTER)

    lay.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Expanding))

    def _show(*args):
        w.a = fix_window(AnimatedDialog(w))
        w.a.resize(200, 200)
        w.a.exec_()

    button.clicked.connect(_show)
    w.show()

    app.exec_()

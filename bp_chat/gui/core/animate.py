
from PyQt5.QtWidgets import (QDialog, QApplication, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLayout, QGridLayout, QSpacerItem, QSizePolicy, QToolButton, QSystemTrayIcon, QMenu,
                             QAction, QSplitter, QStackedWidget)
from PyQt5.QtCore import (QPropertyAnimation, QAbstractAnimation, QRect, QParallelAnimationGroup, Qt, QPoint, QSize,
                          QEvent)
from PyQt5.QtGui import QColor, QLinearGradient, QPainter, QBrush, QIcon


def favicon():
    return QIcon('data/images/favicon.png')

def main_widget(widget:QWidget):
    fix_window(widget)
    widget.setWindowIcon(favicon())
    widget.setAttribute(Qt.WA_DeleteOnClose, False)
    return widget

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
            #parent.setWindowOpacity(0.5)
            shadow_widget = getattr(parent, 'shadow_widget', None)
            if not shadow_widget:
                shadow_widget = ShadowWidget(parent)
            shadow_widget.show()
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
            parent.shadow_widget.hide() #parent.setWindowOpacity(1)


class ShadowWidget(QWidget):

    def __init__(self, parent:QWidget=None):
        super().__init__(parent)

        color = QColor('#555555')
        color.setAlphaF(0.5)

        set_widget_background(self, color)

        parent.shadow_widget = self

        self.move(0, 0)
        self.resize(parent.size())

        parent.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            self.resize(obj.size())

        return super().eventFilter(obj, event)



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

        lay.setColumnStretch(1, 100)

        self.left_widget = None
        self.center_widget = None
        self.right_widget = None

    def set_widget(self, widget, to):
        lay = self.layout()
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


class ImagedButton(QToolButton):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(32, 32)
        self.setAutoRaise(True)
        self.setIconSize(QSize(32, 32))

    @classmethod
    def by_filename(cls, fi):
        obj = cls()
        obj.setIcon(QIcon(fi))
        return obj

    # def paintEvent(self, event):
    #     painter = QPainter(self)
    #     painter.setPen(Qt.NoPen)


# def make_tray_icon(app, parent, main_icon):
#     icon = SystemTrayIcon(main_icon, parent)
#     icon.app = app
#
#     def _on_close(*args):
#         print('_on_close (for tray)')
#         icon.hide()
#
#     app.lastWindowClosed.connect(_on_close)
#
#     icon.show()
#     return icon


class SystemTrayIcon(QSystemTrayIcon):

    app: QApplication = None
    parent_widget: QWidget = None

    def __init__(self, icon, parent, app):
        QSystemTrayIcon.__init__(self, icon, None)

        self.parent_widget = parent
        self.app = app
        # self.parent_widget.tray_icon = self

        self.menu = QMenu(parent)

        exitAction = QAction('Close BP Chat', self)
        exitAction.triggered.connect(self.exit_chat)
        self.menu.addAction(exitAction)

        self.setContextMenu(self.menu)
        self.activated.connect(self.iconActivated)

        app.aboutToQuit.connect(self.close)

    def exit_chat(self):
        # self.close()
        # self.parent_widget.close()
        # self.parent_widget.deleteLater()
        self.parent_widget.hide()

    def iconActivated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.parent_widget.isMinimized():
                if self.parent_widget.was_maximized:
                    self.parent_widget.showMaximized()
                else:
                    self.parent_widget.showNormal()
            else:
                self.parent_widget.showMinimized()

    def close(self):
        self.hide()
        self.deleteLater()


class LeftRightSplitter(QSplitter):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.left_stack = QStackedWidget(self)
        self.right_stack = QStackedWidget(self)

        self.addWidget(self.left_stack)
        self.addWidget(self.right_stack)

    def add_widget(self, widget, to):
        getattr(self, to + '_stack').addWidget(widget)


class TopBottomSplitter(QSplitter):

    def __init__(self, parent=None):
        super().__init__(Qt.PortraitOrientation, parent)

        self.top_stack = QStackedWidget(self)
        self.bottom_stack = QStackedWidget(self)

        self.addWidget(self.top_stack)
        self.addWidget(self.bottom_stack)

    def add_widget(self, widget, to):
        getattr(self, to + '_stack').addWidget(widget)


if __name__=='__main__':

    app = QApplication([])

    w = main_widget(QWidget())
    w.resize(800, 800)
    main_lay = QVBoxLayout(w)
    main_lay.setContentsMargins(0, 0, 0, 0)

    splitter = LeftRightSplitter(w)
    main_lay.addWidget(splitter)

    right_widget = main_widget(QWidget(splitter))
    lay = QVBoxLayout(right_widget)
    lay.setContentsMargins(0, 0, 0, 0)

    splitter.add_widget(right_widget, 'right')

    toolbar = Toolbar(w)
    lay.addWidget(toolbar)

    button = fix_window(QPushButton("Test", w))
    toolbar.set_widget(button, Toolbar.RIGHT)
    toolbar.set_widget(QLabel('Test'), Toolbar.CENTER)

    settings_button = ImagedButton.by_filename("data/images/settings.png")
    settings_button.clicked.connect(lambda *args: app.exit(0))

    toolbar.set_widget(settings_button, Toolbar.LEFT)

    lay.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Expanding))

    def _show(*args):
        w.a = fix_window(AnimatedDialog(w))
        w.a.resize(200, 200)
        w.a.exec_()

    button.clicked.connect(_show)

    w.show()

    tray_icon = SystemTrayIcon(favicon(), w, app)
    tray_icon.show()
    #tray_icon.raise_()
    tray_icon.showMessage("BP Chat is started", "Hello!", favicon())

    app.exec_()

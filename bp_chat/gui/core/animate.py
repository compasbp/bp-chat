
from PyQt5.QtWidgets import (QDialog, QApplication, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLayout, QGridLayout, QSpacerItem, QSizePolicy, QToolButton, QSystemTrayIcon, QMenu,
                             QAction, QSplitter, QStackedWidget)
from PyQt5.QtCore import (QPropertyAnimation, QAbstractAnimation, QRect, QParallelAnimationGroup, Qt, QPoint, QSize,
                          QEvent)
from PyQt5.QtGui import QColor, QLinearGradient, QPainter, QBrush, QIcon

from .draw import draw_rounded_form, draw_shadow_down, draw_shadow_round, set_widget_background


def favicon():
    return QIcon('data/images/favicon.png')

def main_widget(widget:QWidget):
    fix_window(widget)
    widget.was_maximized = False
    widget.setWindowIcon(favicon())
    widget.setAttribute(Qt.WA_DeleteOnClose, False)

    def closeEvent(e):
        if widget.isActiveWindow():
            widget.hide()
            e.ignore()
            return
        else:
            ret = super(widget.__class__, widget).closeEvent(e)
            return ret

    def changeEvent(e):
        if e.type() == QEvent.WindowStateChange:
            if widget.isMaximized():
                widget.was_maximized = True
            elif widget.isMinimized():
                pass
            else:
                widget.was_maximized = False
        return widget.__class__.changeEvent(widget, e)

    #widget.closeEvent = closeEvent
    widget.changeEvent = changeEvent

    return widget

def fix_window(window):
    flags = window.windowFlags()
    flags = int(flags)
    flags &= ~Qt.WindowContextHelpButtonHint
    flags = Qt.WindowFlags(flags)
    window.setWindowFlags(flags)
    return window




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
        self.close()
        self.app.exit(0)
        # self.parent_widget.close()
        # self.parent_widget.deleteLater()
        # self.parent_widget.hide()

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


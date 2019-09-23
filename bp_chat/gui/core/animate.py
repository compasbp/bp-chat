
from PyQt5.QtWidgets import QDialog, QApplication, QPushButton
from PyQt5.QtCore import QPropertyAnimation, QAbstractAnimation, QRect, QParallelAnimationGroup, Qt


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

        duration = 500

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



if __name__=='__main__':

    app = QApplication([])

    w = fix_window(QPushButton("Test"))
    w.resize(800, 800)

    def _show(*args):
        w.a = fix_window(AnimatedDialog(w))
        w.a.resize(200, 200)
        w.a.exec_()

    w.clicked.connect(_show)
    w.show()

    app.exec_()

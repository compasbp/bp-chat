
from PyQt5.QtWidgets import QDialog, QApplication, QPushButton
from PyQt5.QtCore import QPropertyAnimation, QAbstractAnimation, QRect, QParallelAnimationGroup


class AnimatedDialog(QDialog):

    def showEvent(self, event):
        super().showEvent(event)

        duration = 500

        anim1 = QPropertyAnimation(self, b"windowOpacity")
        anim1.setStartValue(0.0)
        anim1.setEndValue(1.0)
        anim1.setDuration(duration)

        anim2 = QPropertyAnimation(self, b"geometry")
        anim2.setDuration(duration)
        anim2.setKeyValueAt(0, QRect(100, 100, 200, 200))
        #anim2.setKeyValueAt(0.8, QRect(250, 250, 100, 30))
        anim2.setKeyValueAt(1, QRect(100, 100, 500, 300))

        self.group = QParallelAnimationGroup(self)
        self.group.addAnimation(anim1)
        self.group.addAnimation(anim2)

        self.group.start(QAbstractAnimation.DeleteWhenStopped)


if __name__=='__main__':

    app = QApplication([])

    w = QPushButton("Test")

    def _show(*args):
        w.a = AnimatedDialog(w)
        w.a.exec_()

    w.clicked.connect(_show)
    w.show()

    app.exec_()

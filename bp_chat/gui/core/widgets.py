from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QToolButton, QStackedLayout,
                             QLabel, QLineEdit, QStackedWidget, QSplitter)
from PyQt5.QtGui import QPainter, QBrush, QColor, QIcon
from PyQt5.QtCore import Qt, QRect, QPoint, QEvent, QSize

from .draw import set_widget_background, draw_shadow_down, draw_shadow_round, draw_rounded_form


class VLayoutWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(0)

    def addWidget(self, widget):
        self.lay.addWidget(widget)



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

        self.stack = QStackedLayout(self)

        self.pages = {}
        self.elements = {}

        self.current_page = self.add_page('first')

        self.down_shadow = DownShadow(parent)
        self.installEventFilter(self.down_shadow)

    def showEvent(self, e):
        ret = super().showEvent(e)
        self.down_shadow.show()
        return ret

    def add_page(self, name):
        page = ToolbarPage(len(self.pages), self)
        self.pages[name] = page
        self.stack.addWidget(page)
        return page

    def set_page(self, name):
        self.stack.setCurrentIndex(self.pages[name].page_num)

    def add_button(self, name, to, iconname, page=None):
        button = ImagedButton.by_filename("data/images/"+iconname+".png")
        self.elements[name] = button
        self.set_widget(button, to, page=page)
        return button

    def add_label(self, name, to, text, page=None):
        label = QLabel(text)
        self.elements[name] = label
        self.set_widget(label, to, page=page)
        return label

    def add_input(self, name, to, page=None):
        edit = QLineEdit()
        self.elements[name] = edit
        self.set_widget(edit, to, page=page)
        return edit

    def set_widget(self, widget, to, page=None):
        if not page:
            page = 'first'
        page = self.pages[page]

        lay = page.lay
        last_widget = getattr(page, to + '_widget')

        if last_widget:
            lay.removeWidget(last_widget)

        setattr(page, to + '_widget', widget)

        lay.addWidget(widget, 0, self.POSES[to])

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)

        start_color = QColor('#777777')
        start_color.setAlphaF(0.5)

        brush = QBrush(start_color)
        painter.setBrush(brush)
        painter.drawRect(QRect(QPoint(0, self.height()-1), QPoint(self.width(), self.height())))


class ToolbarPage(QWidget):

    def __init__(self, page_num, parent=None):
        super().__init__(parent)
        self.page_num = page_num

        self.lay = QGridLayout(self)
        self.lay.setColumnStretch(1, 100)
        self.left_widget = None
        self.right_widget = None
        self.center_widget = None


class DownShadow(QWidget):

    h = 20

    def eventFilter(self, obj, e):
        if e.type() == QEvent.Resize:
            self.resize(obj.width(), self.h)
            self.move(obj.x(), obj.y()+obj.height())
        return super().eventFilter(obj, e)

    def paintEvent(self, event):
        painter = QPainter(self)
        sz = self.size()
        draw_shadow_down(painter, (0, 0), (sz.width(), sz.height()))


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



class LeftRightSplitter(QSplitter):

    LEFT = 'left'
    RIGHT = 'right'

    def __init__(self, parent=None):
        super().__init__(parent)

        self.left_stack = QStackedWidget(self)
        self.right_stack = QStackedWidget(self)

        self.addWidget(self.left_stack)
        self.addWidget(self.right_stack)

        self.setHandleWidth(0)

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


class InfoLabel(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(50)

    def paintEvent(self, event):
        #ret = super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        sz = self.size()
        padding = 5
        width = sz.width() - padding*2
        height = 30
        r = height / 2
        shadow_ln = 10

        draw_shadow_round(painter, (r+padding-1, height), shadow_ln, part='left')
        draw_shadow_round(painter, (padding+width-r+1, height), shadow_ln, part='right')
        draw_rounded_form(painter, (padding, 0), (width, height))
        draw_shadow_down(painter, (padding+r, height), (width-r*2, shadow_ln))

        painter.setPen(QColor(255, 255, 255))
        #font = painter.font()
        # font = QFont("Arial")
        # font.setPixelSize(font_pixel_size)
        #font.setPointSize(6)
        #font.setBold(True)
        #painter.setFont(font)
        painter.drawText(30, 18, self.text())
        #return ret

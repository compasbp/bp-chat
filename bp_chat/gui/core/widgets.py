from os.path import basename

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QToolButton, QStackedLayout,
                             QLabel, QLineEdit, QStackedWidget, QSplitter, QTextEdit, QFrame)
from PyQt5.QtGui import QPainter, QBrush, QColor, QIcon, QPen
from PyQt5.QtCore import Qt, QRect, QRectF, QPoint, QEvent, QSize, QAbstractAnimation, pyqtSignal, QPointF

from .draw import (set_widget_background, draw_shadow_round, draw_rounded_form,
                   draw_shadow, draw_shadow_down, SHADOW_DOWN, SHADOW_RIGHT, SHADOW_UP, IconDrawer)
from ..models.element_parts import PHLayout, SimpleIcon, PBase


class VLayoutWidget(QWidget):

    MARGINS = (0, 0, 0, 0)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(*self.MARGINS)
        self.lay.setSpacing(0)

    def addWidget(self, widget):
        self.lay.addWidget(widget)

    def addLayout(self, layout):
        self.lay.addLayout(layout)


class PagedWidget(QStackedWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.pages = {}
        self.layout().setContentsMargins(0, 0, 0, 0)

    def add_page(self, name, widget):
        self.pages[name] = self.count()
        self.addWidget(widget)
        return widget

    def set_page(self, name):
        self.setCurrentIndex(self.pages[name])


class Toolbar(QWidget):

    LEFT = 'left'
    RIGHT = 'right'
    CENTER = 'center'
    BOTTOM = 'bottom'
    TOP = 'top'

    LINE_HEIGHT = 60

    POSES = {
        LEFT: 0, CENTER: 1, RIGHT: 2
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        set_widget_background(self, '#ffc107')

        self.lay = QVBoxLayout(self)
        self.lay.setSpacing(0)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.stack_top = QStackedLayout()
        self.stack_top.setContentsMargins(0, 0, 0, 0)
        self.stack_bottom = QStackedLayout()
        self.stack_bottom.setContentsMargins(0, 0, 0, 0)
        self.lay.addLayout(self.stack_top)
        self.lay.addLayout(self.stack_bottom)

        self.pages_top = {}
        self.pages_bottom = {}
        self.elements = {}

        self.update_height()

        self.add_page('first')

        self.down_shadow = SideShadow(parent, side=SideShadow.DOWN)
        self.down_shadow.install(self)

    def update_height(self):
        h = self.LINE_HEIGHT
        if len(self.pages_bottom) > 0:
            h *= 2
        self.setMaximumHeight(h)
        self.setMinimumHeight(h)

    def showEvent(self, e):
        ret = super().showEvent(e)
        self.down_shadow.show()
        return ret

    def add_page(self, name, part=TOP):
        page = ToolbarPage(len(getattr(self, 'pages_' + part)), self)
        getattr(self, 'pages_' + part)[name] = page
        getattr(self, 'stack_' + part).addWidget(page)
        return page

    def set_page(self, name, part=TOP):
        getattr(self, 'stack_' + part).setCurrentIndex(getattr(self, 'pages_' + part)[name].page_num)

    def add_button(self, name, to, iconname, page=None, part=TOP):
        button = ImagedButton.by_filename("data/images/"+iconname+".png")
        self.elements[name] = button
        self.set_widget(button, to, page=page, part=part)
        return button

    def add_buttons_group(self, name, to=CENTER, page=None, part=TOP):
        button_group = ButtonsGroup()
        self.elements[name] = button_group
        self.set_widget(button_group, to, page=page, part=part)
        return button_group

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

    def set_text(self, name, text):
        self.elements[name].setText(text)

    def set_widget(self, widget, to, page=None, part=TOP):
        if not page:
            page = 'first'

        if part == Toolbar.BOTTOM and len(self.pages_bottom) == 0:
            self.add_page('first', part=Toolbar.BOTTOM)
            self.update_height()

        page = getattr(self, 'pages_' + part)[page]

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
        self.lay.setContentsMargins(10, 0, 10, 0)
        self.left_widget = None
        self.right_widget = None
        self.center_widget = None

        h = 60
        self.setMaximumHeight(h)
        self.setMinimumHeight(h)


class ButtonsGroup(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lay = QHBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.buttons = {}

    def add_button(self, name, iconname, text=None):
        button = ImagedButton.by_filename("data/images/"+iconname+".png")
        if text:
            button.setText(text)
        self.buttons[name] = button
        self.lay.addWidget(button)
        return button


class SideShadow(QWidget):

    DOWN = SHADOW_DOWN
    RIGHT = SHADOW_RIGHT
    UP = SHADOW_UP

    _side = DOWN

    def __init__(self, parent, side=DOWN, h=10):
        super().__init__(parent)

        self.h = h
        self._side = side

    def install(self, parent):
        parent.installEventFilter(self)

    def eventFilter(self, obj, e):
        if e.type() == QEvent.Resize:
            #print(1, self._side)

            if self._side == SideShadow.DOWN:
                size = (obj.width(), self.h)
                self.move(obj.x(), obj.y()+obj.height())
            elif self._side == SideShadow.UP:
                size = (obj.width(), self.h)
                self.move(obj.x(), obj.y() - size[1])
            else:
                size = (self.h, obj.height())
                self.move(obj.x() + obj.width(), obj.y())

            self.resize(*size)
            #self.setMinimumSize(QSize(*size))

        return super().eventFilter(obj, e)

    def paintEvent(self, event):
        #print(2)
        painter = QPainter(self)
        sz = self.size()

        draw_shadow(painter, (0, 0), (sz.width(), sz.height()), side=self._side)

        start_p = QPoint(0, 0)
        end_p = QPoint(sz.width(), sz.height())
        #print(f'REDRAW ({start_p.x()},{start_p.y()}) ({end_p.x()},{end_p.y()})')


class ImagedButton(QToolButton):

    def __init__(self, parent=None, size=(50, 50), icon_size=(32, 32)):
        super().__init__(parent)

        self.icon_drawer = IconDrawer(self)

        self.setFixedSize(*size)
        self.setAutoRaise(True)
        self.setIconSize(QSize(*icon_size))

    @classmethod
    def by_iconname(cls, iconname):
        return ImagedButton.by_filename("data/images/"+iconname+".png")

    @classmethod
    def by_filename(cls, fi):
        obj = cls()
        obj.setIcon(QIcon(fi))
        return obj

    def paintEvent(self, e):
        self.icon_drawer.draw_icon(QPainter(self), (self.width(), self.height()), self.underMouse())

    def enterEvent(self, e):
        ret = super().enterEvent(e)
        self.icon_drawer.start_animation()
        return ret



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



class PLabelText(PBase):

    def get_size(self, item, delegate):
        r = self.fm.boundingRect("W")
        return None, r.height()

    def _draw(self, painter: QPainter, delegate, item, rect_tuple: tuple):
        left, top, right, bottom = rect_tuple

        pen = QPen()
        pen.setWidth(1)
        pen.setColor(QColor(30, 30, 30))
        painter.setPen(pen)

        font = self.font
        painter.setFont(font)

        second_text = item.text()

        _text = second_text.replace("\n", " ").replace("\r", "").replace("\t", " ")
        while "  " in _text:
            _text = _text.replace("  ", " ")

        brect = self.fm.boundingRect(left, 0, 9999, 50, Qt.Horizontal, _text)
        if brect.right() > right - 10:  # FIXME
            max_len = int((right - left) / 6)
            _text = _text[:max_len] + "..."

        self.draw_line(painter, _text, left, top, right, bottom)

    @property
    def font_size(self):
        return 12


class PLabelLayout(PHLayout):

    def _draw(self, painter: QPainter, delegate, item, rect_tuple: tuple):
        left, top, right, bottom = rect_tuple

        rect = QRectF(QPointF(left, top), QPointF(right, bottom))

        _background_color = "#cccccc"
        if item._background_color:
            _background_color = item._background_color

        _color = "#555555"
        if item._color:
            _color = item._color

        painter.setPen(QColor(_color))
        painter.setBrush(QColor(_background_color))

        painter.drawRect(rect)

        super()._draw(painter, delegate, item, rect_tuple)


class PLabelExpand(SimpleIcon):

    def need_show(self, item, delegate):
        return True

    def get_icon_name(self, item, delegate):
        return 'expand'


class AutoPos:
    NO = 0
    TOP = 1
    BOTTOM = 2

    HEIGHT = None
    WIDTH = None

    def init_auto_pos(self, parent, auto_pos):
        self.auto_pos = auto_pos
        if auto_pos and parent:
            parent.installEventFilter(self)

    def eventFilter(self, obj, e):
        if e.type() == QEvent.Resize:
            h = obj.height() if self.HEIGHT == None else self.HEIGHT
            w = obj.width() if self.WIDTH == None else self.WIDTH
            self.resize(QSize(w, h))
            if self.auto_pos == AutoPos.TOP:
                self.move(0, 0)
            elif self.auto_pos == AutoPos.BOTTOM:
                self.move(0, obj.height()-h)
        #return super().eventFilter(obj, e)
        return False


class InfoLabel(QLabel, AutoPos):

    _PARTS = PLabelLayout(
        PLabelExpand(),
        PLabelText(margin_left=10, margin_right=10),
        margin_left=20, margin_right=20, margin_bottom=10
    )
    _background_color = None
    _color = None

    def __init__(self, parent=None, auto_pos=AutoPos.NO):
        super().__init__(parent)
        self.setMinimumHeight(30)
        self.init_auto_pos(parent, auto_pos)
        self.setCursor(Qt.PointingHandCursor)

    @property
    def HEIGHT(self):
        return self.height()

    def set_background(self, color):
        self._background_color = color

    def set_color(self, color):
        self._color = color

    def paintEvent(self, event):
        #ret = super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        sz = self.size()

        self._PARTS.draw(painter, self, self, (0, 0, sz.width(), sz.height()))

        # padding = 5
        # width = sz.width() - padding*2
        # height = 30
        # r = height / 2
        # shadow_ln = 10
        #
        # draw_shadow_round(painter, (r+padding-1, height), shadow_ln, part='left')
        # draw_shadow_round(painter, (padding+width-r+1, height), shadow_ln, part='right')
        # draw_rounded_form(painter, (padding, 0), (width, height))
        # draw_shadow_down(painter, (padding+r, height), (width-r*2, shadow_ln))
        #
        # painter.setPen(QColor(255, 255, 255))
        # #font = painter.font()
        # # font = QFont("Arial")
        # # font.setPixelSize(font_pixel_size)
        # #font.setPointSize(6)
        # #font.setBold(True)
        # #painter.setFont(font)
        # painter.drawText(30, 18, self.text())
        # #return ret

    def _on_mouse_click(self):
        pass

    def set_on_mouse_click_callback(self, callback):
        self._on_mouse_click = callback

    def event(self, e):
        if e.type() == QEvent.MouseButtonPress:
            self._on_mouse_click()
        return super().event(e)


class MessageInputWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lay = QVBoxLayout(self)
        self.lay.setSpacing(0)
        self.lay.setContentsMargins(0, 1, 0, 0)
        self.stack_top = QStackedLayout()
        self.stack_top.setContentsMargins(0, 0, 0, 0)
        self.stack_bottom = QStackedLayout()
        self.stack_bottom.setContentsMargins(0, 0, 0, 0)
        self.lay.addLayout(self.stack_top)
        self.lay.addLayout(self.stack_bottom)

        self.input_line = InputLine(self)
        self.stack_bottom.addWidget(self.input_line)

        self.files_line = FilesLine(self)
        #self.files_line.add_file("Some file.png", "file")
        self.stack_top.addWidget(self.files_line)

        self.setMaximumHeight(100)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        if (e.mimeData().hasUrls()):
            e.acceptProposedAction()

    def dropEvent(self, e):
        for url in e.mimeData().urls():
            filename = url.toLocalFile()
            print("Dropped file:", filename)
            fi = basename(filename)
            if self.files_line.count() < 1:
                self.files_line.add_file(fi, "file")

    def paintEvent(self, QPaintEvent):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)

        start_color = QColor('#777777')
        start_color.setAlphaF(0.5)

        painter.setBrush(QBrush(start_color))
        painter.drawRect(QRect(QPoint(0, 0), QPoint(self.width(), 0)))


class FilesLine(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lay = QHBoxLayout(self)
        self.lay.setSpacing(0)
        self.lay.setContentsMargins(0, 0, 0, 0)

        set_widget_background(self, '#eeeeee')

    def add_file(self, filename, iconname=None):
        file_item = FileItemWidget(filename, iconname, self)
        self.lay.addWidget(file_item)

    def count(self):
        return self.lay.count()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setPen(QColor('#dddddd'))
        painter.drawLine(0, self.height()-1, self.width(), self.height()-1)


class FileItemWidget(QWidget):

    def __init__(self, filename, iconname=None, parent=None):
        super().__init__(parent)

        self.lay = QHBoxLayout(self)

        self.lay.setSpacing(0)
        self.lay.setContentsMargins(0, 0, 0, 0)

        self.button = ImagedButton.by_iconname(iconname)
        self.lay.addWidget(self.button)

        self.label = QLabel(filename)
        self.lay.addWidget(self.label)

        self.close_button = ImagedButton.by_iconname('cancel')
        self.lay.addWidget(self.close_button)
        self.close_button.clicked.connect(self.remove_file)

    def remove_file(self):
        lay:QHBoxLayout = self.parent().lay
        lay.removeWidget(self)


class InputLine(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lay = QGridLayout(self)
        self.lay.setColumnStretch(0, 100)
        self.lay.setContentsMargins(0, 0, 0, 0)

        #set_widget_background(self, '#ffffff')

        self.text_edit = QTextEdit()
        self.text_edit.setFrameShape(QFrame.NoFrame)
        set_widget_background(self.text_edit, '#ffffff')
        self.text_edit.setStyleSheet("QTextEdit { padding-left:10; padding-top:10; padding-bottom:10; padding-right:10}")
        self.send_button = ImagedButton.by_iconname("send")
        self.lay.addWidget(self.text_edit, 0, 0)
        self.lay.addWidget(self.send_button, 0, 1)

        self.text_edit.setAcceptDrops(False)
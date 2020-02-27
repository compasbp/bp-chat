from os.path import abspath

from PyQt5.QtGui import (QColor, QFont, QPainter, QLinearGradient, QBrush, QRadialGradient,
                         QBitmap, QIcon, QPixmap)
from PyQt5.QtCore import (QPointF, Qt, QPoint, QRect, QRectF, QSize, QAbstractAnimation,
                          pyqtSignal, QEvent)
from PyQt5.QtWidgets import QWidget


def set_widget_background(widget, color):
    if type(color) == str:
        color = QColor(color)
    palette = widget.palette()
    palette.setColor(widget.backgroundRole(), color)
    widget.setPalette(palette)
    widget.setAutoFillBackground(True)
    return palette


def draw_badges(painter, badges, left, top, font_pixel_size=10, factor=1, muted=False, plus=True, bcolor=None):

    # draw badges
    pen = painter.pen()
    pen.setWidth(1)
    painter.setPen(pen)

    badges = str(badges)

    if bcolor:
        main_color = QColor(bcolor)
    else:
        main_color = QColor(150, 150, 150) if muted else QColor(255, 100, 100)

    painter.setPen(QColor(255, 100, 100, 0))
    painter.setBrush(main_color)
    painter.drawEllipse(QPointF(left + 6*factor, top - 3*factor), 8*factor, 8*factor)

    if len(badges) > 1:
        left_minus = (6*factor) * (len(badges)-1)
        left -= left_minus
        painter.drawEllipse(QPointF(left + 6*factor, top - 3*factor), 8*factor, 8*factor)
        painter.fillRect(left+6*factor, top - (3 + 8)*factor, left_minus, (8*2)*factor, main_color)

    painter.setPen(QColor(255, 255, 255))
    #font = painter.font()
    font = QFont("Arial")
    font.setPixelSize(font_pixel_size)
    #font.setPointSize(6)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(left, top, "+{}".format(badges) if plus else badges)


def draw_rounded_form(painter, pos, size):

    # draw badges
    pen = painter.pen()
    pen.setWidth(1)
    painter.setPen(pen)

    left, top = pos
    width, height = size
    center = (width/2, height/2)
    r = min(center)

    main_color = QColor(150, 150, 150)

    painter.setPen(QColor(255, 100, 100, 0))
    painter.setBrush(main_color)
    painter.drawEllipse(QPointF(left+r, top+r), r, r)

    if width > height:
        #left_minus = (6*factor) * (len(badges)-1)
        #left -= left_minus
        painter.drawEllipse(QPointF(left+width-r, r), r, r)
        painter.fillRect(left+r, top, width-r*2, height, main_color)

    # painter.setPen(QColor(255, 255, 255))
    # #font = painter.font()
    # font = QFont("Arial")
    # font.setPixelSize(font_pixel_size)
    # #font.setPointSize(6)
    # font.setBold(True)
    # painter.setFont(font)
    # painter.drawText(left, top, "+{}".format(badges))

def draw_shadow_down(painter: QPainter, pos, size):
    draw_shadow(painter, pos, size, side=SHADOW_DOWN)

def draw_shadow_right(painter: QPainter, pos, size):
    draw_shadow(painter, pos, size, side=SHADOW_RIGHT)

SHADOW_DOWN = 0
SHADOW_RIGHT = 1
SHADOW_UP = 2

def draw_shadow(painter: QPainter, pos, size, side=SHADOW_DOWN):
    left, top = pos
    width, height = g_width, g_height = size

    painter.setPen(Qt.NoPen)

    start_color = QColor('#777777')
    start_color.setAlphaF(0.3)

    end_color = QColor('#777777')
    end_color.setAlphaF(0.0)

    start_p = QPoint(left, top)
    end_p = QPoint(left + width, top + height)

    if side == SHADOW_DOWN:
        g_width = 0
    elif side == SHADOW_UP:
        g_width = 0
        start_color, end_color = end_color, start_color
    else:
        g_height = 0

    gradient = QLinearGradient(left, top, g_width, g_height)
    gradient.setColorAt(0.0, start_color)
    gradient.setColorAt(1.0, end_color)
    brush = QBrush(gradient)

    painter.setBrush(brush)
    painter.drawRect(QRect(start_p, end_p))

def draw_shadow_round(painter: QPainter, center, radius, part=None):
    x, y = center
    r = radius

    painter.setPen(Qt.NoPen)

    start_color = QColor('#777777')
    start_color.setAlphaF(0.3)

    end_color = QColor('#777777')
    end_color.setAlphaF(0.0)
    #end_color = self.parentWidget().palette().color(self.parentWidget().backgroundRole())

    gradient = QRadialGradient(QPointF(x, y), r)
    gradient.setColorAt(0.0, start_color)
    gradient.setColorAt(1.0, end_color)
    brush = QBrush(gradient)

    right = x + r
    if part == 'left':
        right = x

    left = x - r
    if part == 'right':
        left = x

    #brush = QBrush(start_color)
    painter.setBrush(brush)
    painter.drawRect(QRect(QPoint(left, y - r), QPoint(right, y + r)))
    #painter.drawEllipse(QPointF(left, top), radius, radius)


def get_round_mask(size=(50, 50), to_size=(50, 50), border_radius=None):
    _w, _h = size
    w, h = to_size

    map = QBitmap(_w, _h)

    painter = QPainter(map)
    painter.setRenderHint(QPainter.Antialiasing)

    painter.setPen(QColor(0, 0, 0))
    painter.setBrush(QColor(0, 0, 0))

    left = 0
    if _w > _h:
        left = int((_w - _h) / 2)

    rect = QRect(left, 0, w, h)
    full_rect = QRect(0, 0, _w, _h)
    painter.fillRect(full_rect, QColor(255, 255, 255))

    if border_radius:
        br = border_radius
        #full_rect = QRect(br, br, _w - br * 2, _h - br * 2)
        for i in ((br, 0, _w-br*2, _h), (0, br, _w, _h-br*2)):
            painter.fillRect(QRect(*i), QColor(0, 0, 0))

        for x, y in ((br, br), (_w-br, br), (_w-br, _h-br), (br, _h-br)):
            painter.drawEllipse(QPoint(x, y), br, br)
    else:
        painter.drawEllipse(rect)

    painter.end()

    return map

def color_from_hex(hex_color):
    if type(hex_color) == str:
        hex_color = QColor(hex_color)
    return hex_color


def pixmap_from_file(icon_name, to_width, to_height):
    icon = icon_from_file(icon_name)
    return icon.pixmap(QSize(to_width, to_height))

def pixmap_from_icon(icon, to_width, to_height):
    return icon.pixmap(QSize(to_width, to_height))

def icon_from_file(icon_name):
    return QIcon(path_to_images() + "/" +
                 icon_name + ".png")

def path_to_images():
    #return ':/images/data/images/'
    return abspath('data/images/')


class IconDrawer:

    def __init__(self, parent):
        self.parent = parent
        self.animation = None

    def draw_icon(self, painter: QPainter, size: tuple, under_mouse: bool, icon: QIcon=None, icon_size: tuple=None):
        painter.setRenderHint(QPainter.Antialiasing)

        if not icon_size:
            icon_size = (self.parent.iconSize().width(), self.parent.iconSize().height())
        _icon_size = QSize(*icon_size)
        if not icon:
            icon: QIcon = self.parent.icon()

        _actual_size: QSize = icon.actualSize(_icon_size)
        actual_size = (_actual_size.width(), _actual_size.height())

        pixmap = icon.pixmap(_icon_size)

        alpha = 0
        if self.animation:
            alpha = self.animation.alpha

        self.draw_pixmap(painter, pixmap, (0, 0), size, under_mouse, icon_size, actual_size, alpha)

    @staticmethod
    def draw_pixmap(painter: QPainter, pixmap: QPixmap, pos: tuple, size: tuple, under_mouse: bool,
                    icon_size: tuple, actual_size: tuple, alpha: float):

        dx, dy = size[0] - icon_size[0], size[1] - icon_size[1]
        dw, dh = icon_size[0] - actual_size[0], icon_size[1] - actual_size[1]

        if under_mouse:
            c = QColor('#ffffff00')
            c.setAlpha(0)
            painter.setPen(c)
            c2 = QColor('#000000')
            c2.setAlphaF(alpha*0.3)
            painter.setBrush(c2)
            painter.drawEllipse(QRectF(pos[0], pos[1], size[0], size[1]))

        painter.drawPixmap(pos[0] + dx / 2 + dw / 2, pos[1] + dy / 2 + dh / 2, pixmap)

        # painter.setBrush(c)
        # painter.setPen(QColor('#000000'))
        # painter.drawRect(pos[0], pos[1], size[0], size[1])

    def start_animation(self):
        if self.animation:
            self.animation.stop()
            self.animation.deleteLater()
        self.animation = IconRoundAnimation(self.parent)
        self.animation.need_update.connect(self.parent.repaint)
        self.animation.start()


class IconRoundAnimation(QAbstractAnimation):

    need_update = pyqtSignal()
    alpha = 0
    DURATION = 300

    def duration(self):
        return self.DURATION

    def updateCurrentTime(self, currentTime):
        self.alpha = currentTime / float(self.DURATION) / 2.0
        self.need_update.emit()


class LoadAnimation(QAbstractAnimation):

    need_update = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.poses = [0, 0, 0]
        self.side = 1
        self.widget = None

    def start(self, *args):
        self.widget = LoadAnimationWidget(self, self.parent())
        self.need_update.connect(self.widget.update_pos)
        self.widget.show()
        super().start()

    def stop(self):
        super().stop()
        if self.widget:
            self.widget.deleteLater()

    def duration(self):
        return -1

    def updateCurrentTime(self, currentTime):
        if currentTime > 1000:
            self.side = -self.side
            currentTime = 0
            self.setCurrentTime(0)

        if self.side < 0:
            currentTime = 1000 - currentTime
        #a, b, c = self.poses
        a = currentTime / 100.0
        b = currentTime / 100.0 - currentTime / 200.0
        c = currentTime / 100.0 + currentTime / 200.0
        self.poses[:] = [a*3, b, c]
        #print(self.poses)

        self.need_update.emit()


class LoadAnimationWidget(QWidget):

    def __init__(self, animation: LoadAnimation, parent:QWidget=None):
        super().__init__(parent)

        self.animation = animation
        parent.installEventFilter(self)

        self.resize(10, 10)

    def eventFilter(self, obj, e:QEvent):
        if e.type() == QEvent.Resize:
            self.update_pos()
        return super().eventFilter(obj, e)

    def update_pos(self):
        y = self.parent().height()/2 + self.animation.poses[0]
        self.move(self.parent().width()/2, y)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        c = QColor('#ffffff')
        c.setAlpha(0)
        painter.setPen((c))
        painter.setBrush(QColor('#ff0000'))
        painter.drawEllipse(QRectF(0, 0, self.width(), self.height()))

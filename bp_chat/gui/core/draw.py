from os.path import abspath

from PyQt5.QtGui import (QColor, QFont, QPainter, QLinearGradient, QBrush, QRadialGradient,
                         QBitmap, QIcon)
from PyQt5.QtCore import QPointF, Qt, QPoint, QRect, QSize


def set_widget_background(widget, color):
    if type(color) == str:
        color = QColor(color)
    palette = widget.palette()
    palette.setColor(widget.backgroundRole(), color)
    widget.setPalette(palette)
    widget.setAutoFillBackground(True)
    return palette


def draw_badges(painter, badges, left, top, font_pixel_size=10, factor=1, muted=False):

    # draw badges
    pen = painter.pen()
    pen.setWidth(1)
    painter.setPen(pen)

    badges = str(badges)

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
    painter.drawText(left, top, "+{}".format(badges))


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
    left, top = pos
    width, height = size

    painter.setPen(Qt.NoPen)

    start_color = QColor('#777777')
    start_color.setAlphaF(0.3)

    end_color = QColor('#777777')
    end_color.setAlphaF(0.0)
    #end_color = self.parentWidget().palette().color(self.parentWidget().backgroundRole())

    gradient = QLinearGradient()
    gradient.setColorAt(0.0, start_color)
    gradient.setColorAt(1.0, end_color)
    gradient.setStart(QPoint(left, top))
    gradient.setFinalStop(QPoint(left, top+height))
    brush = QBrush(gradient)

    #brush = QBrush(start_color)
    painter.setBrush(brush)
    painter.drawRect(QRect(QPoint(left, top), QPoint(left+width, top+height)))

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
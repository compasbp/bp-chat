from PyQt5.QtGui import QColor, QFont, QPainter, QLinearGradient, QBrush, QRadialGradient
from PyQt5.QtCore import QPointF, Qt, QPoint, QRect


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
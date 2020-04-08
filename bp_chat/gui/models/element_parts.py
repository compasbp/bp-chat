from PyQt5.QtGui import QPainter, QPixmap, QColor, QFontMetrics
from PyQt5.QtCore import QPointF, Qt, QRectF

from bp_chat.gui.core.draw import color_from_hex, pixmap_from_file, IconDrawer


class PBase:

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def draw(self, painter:QPainter, delegate, item, rect_tuple:tuple):
        pass


class PLayout(PBase):

    VERTICAL = 0
    HORIZONTAL = 1

    direction = None

    def __init__(self, *childs, **kwargs):
        super().__init__(**kwargs)
        self.childs = childs
        #self.calced_sizes = [None for _ in childs]
        #self.calced_size_situation = None

    def get_calced_sizes(self, item, size_tuple):
        #if getattr(item, 'calced_size_situation', None) != size_tuple:

        calced_sizes = [None for _ in self.childs]

        strong_w = 0
        lays = []
        len_i = self.get_length_i_for_calc()
        for i, child in enumerate(self.childs):
            w = child.get_size(item)[len_i]
            if len_i == 0:
                strong_w += child.kwargs.get('margin_left', 0) + child.kwargs.get('margin_right', 0)
            else:
                strong_w += child.kwargs.get('margin_top', 0) + child.kwargs.get('margin_top', 0)
            if w:
                strong_w += w
                calced_sizes[i] = w
            else:
                lays.append(i)

        lays_count = len(lays)
        if lays_count > 0:
            lays_w = size_tuple[len_i] - strong_w
            lay_w = lays_w / float(lays_count)

            for i in lays:
                calced_sizes[i] = lay_w

        #     item.calced_size_situation = size_tuple
        #     item.calced_sizes = calced_sizes
        #
        # return self.calced_sizes

        return calced_sizes

    def get_length_i_for_calc(self):
        return None

    def get_size(self, item):
        return None, None


class PHLayout(PLayout):

    direction = PLayout.HORIZONTAL

    def get_length_i_for_calc(self):
        return 0

    def draw(self, painter: QPainter, delegate, item, rect_tuple: tuple):
        left, top, right, bottom = rect_tuple

        calced_sizes = self.get_calced_sizes(item, (right-left, bottom-top))

        l = left
        for i, child in enumerate(self.childs):
            w = calced_sizes[i]
            ml, mr = child.kwargs.get('margin_left', 0), child.kwargs.get('margin_right', 0)
            mt, _ = child.kwargs.get('margin_top', 0), child.kwargs.get('margin_bottom', 0)
            l += ml
            if w:
                r = l + w
            else:
                r = right
            child.draw(painter, delegate, item, (l, top+mt, r, bottom))
            r += mr
            l = r
            if l >= right:
                break


class PVLayout(PLayout):

    direction = PLayout.VERTICAL

    def get_length_i_for_calc(self):
        return 1

    def draw(self, painter: QPainter, delegate, item, rect_tuple: tuple):
        left, top, right, bottom = rect_tuple

        calced_sizes = self.get_calced_sizes(item, (right - left, bottom - top))

        t = top
        for i, child in enumerate(self.childs):
            h = calced_sizes[i]
            ml, _ = child.kwargs.get('margin_left', 0), child.kwargs.get('margin_right', 0)
            mt, mb = child.kwargs.get('margin_top', 0), child.kwargs.get('margin_bottom', 0)
            t += mt
            if h:
                b = t + h
            else:
                b = bottom
            child.draw(painter, delegate, item, (left+ml, t, right, b))
            b += mb
            t = b
            if t >= bottom:
                break


class PChatImage(PBase):

    def get_size(self, item):
        return 50, 50

    def draw(self, painter: QPainter, delegate, item, rect_tuple: tuple):
        w, h = self.get_size(item)
        self.drawRound(painter, delegate, item, rect_tuple[0], rect_tuple[1], w, h)
        self.drawImage(painter, delegate, item, rect_tuple[0], rect_tuple[1], w, h)
        self.drawStatus(painter, delegate, item, rect_tuple[0], rect_tuple[1], w, h)

    def drawRound(self, painter, delegate, item, left, top, w, h):
        round_color = self.color_from_item(item)
        if round_color:
            iw = w #self.image_width()
            ir = iw / 2
            painter.setPen(round_color)
            painter.setBrush(round_color)
            painter.drawEllipse(QPointF(left + ir, top + ir), ir, ir)

    def drawImage(self, painter, delegate, item, left, top, w, h):
        _image_left_add = 0
        iw = w #self.image_width()

        pixmap = item.getPixmap()
        is_simple_icon = False
        if type(pixmap) == str:
            pixmap = pixmap_from_file(pixmap, iw, iw)
            is_simple_icon = True
        if pixmap:
            pixmap: QPixmap
            if is_simple_icon:
                pixmap = pixmap.scaledToWidth(32/50*iw, Qt.SmoothTransformation)
            sz = pixmap.size()
            actual_size = (sz.width(), sz.height())
            IconDrawer.draw_pixmap(painter, pixmap, (left, top), size=(iw, iw),
                    under_mouse=delegate._is_under_mouse(item),
                    icon_size=(iw, iw), actual_size=actual_size, alpha=1.0)

    def drawStatus(self, painter, delegate, item, left, top, w, h):
        pen = painter.pen()

        status_color = item.getStatusColor()
        if status_color:

            if type(status_color) == str:
                status_color = color_from_hex(status_color)

            pen.setWidth(2)
            pen.setColor(QColor(255, 255, 255))

            painter.setPen(pen)
            painter.setBrush(status_color)
            painter.drawEllipse(QPointF(left + 45 + 8, top + 40 + 8), 6, 6)

    def color_from_item(self, item):
        item_color = item.getColor()
        if item_color:

            if type(item_color) == str:
                item_color = color_from_hex(item_color)

            return item_color


class PChatDownLine(PBase):

    def get_size(self, item):
        return None, 1

    def draw(self, painter: QPainter, delegate, item, rect_tuple: tuple):
        left, top, right, bottom = rect_tuple
        painter.setPen(QColor(220, 220, 220))
        painter.drawLine(left, bottom, right - 10, bottom)


class PLogin(PBase):

    def get_size(self, item):
        return None, 20

    def draw(self, painter: QPainter, delegate, item, rect_tuple: tuple):
        left, top, right, bottom = rect_tuple

        pen, font = delegate.prepare_pen_and_font_for_name(painter, item)
        painter.setPen(pen)
        painter.setFont(font)

        self.draw_name(painter, delegate, item, left, top, right)

    def draw_name(self, painter, delegate, item, left, top, right):
        _name = item.getName()
        _nick = item.getNick()

        brect = painter.boundingRect(QRectF(left, 0, 9999, 50), _name)
        if brect.right() >= right:
            max_len = int((right - left) / 10)
            _name = _name[:max_len] + "..."

        painter.drawText(left, top+16, _name)

        # if _nick and _nick != _name:
        #     draw_badges(painter, _nick, left+34, top+55, font_pixel_size=10,
        #                 bcolor='#7777cc', plus=False, factor=0.6)


class PLastMessage(PBase):

    def get_size(self, item):
        return 20, 20

    def draw(self, painter: QPainter, delegate, item, rect_tuple: tuple):
        left, top, right, bottom = rect_tuple

        painter.setPen(delegate.message_text_color())

        font = delegate.prepareMessageFont()
        painter.setFont(font)

        second_text = item.getSecondText()

        metrics = QFontMetrics(font)

        _text = second_text.replace("\n", " ")
        while "  " in _text:
            _text = _text.replace("  ", " ")

        brect = metrics.boundingRect(left, 0, 9999, 50, Qt.Horizontal, _text)
        if brect.right() > right - 10:  # FIXME
            max_len = int((right - left) / 6)
            _text = _text[:max_len] + "..."

        painter.drawText(left, top, second_text)


class PLastTime(PBase):

    def get_size(self, item):
        return 20, 20

    def draw(self, painter: QPainter, delegate,item, rect_tuple: tuple):
        pass

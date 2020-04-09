from PyQt5.QtGui import QPainter, QPixmap, QColor, QFontMetrics, QFont, QPen
from PyQt5.QtCore import QPointF, Qt, QRectF

from bp_chat.gui.core.draw import color_from_hex, pixmap_from_file, IconDrawer


class PBase:

    _font = None
    _pen = None
    _fm = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def draw(self, painter: QPainter, delegate, item, rect_tuple: tuple):
        if self.debug:
            print('{} - r:{} h:{}'.format(self.__class__.__name__, rect_tuple, rect_tuple[3]-rect_tuple[1]))
            painter.setRenderHint(QPainter.NonCosmeticDefaultPen)
            painter.setPen(QColor(220, 20, 20))
            painter.setBrush(QColor(250, 250, 250))
            painter.drawRect(QRectF(QPointF(*rect_tuple[:2]), QPointF(rect_tuple[2]-1, rect_tuple[3]-1)))
            painter.setRenderHint(QPainter.Antialiasing)
        self._draw(painter, delegate, item, rect_tuple)

    def _draw(self, painter: QPainter, delegate, item, rect_tuple: tuple):
        pass

    def __getattr__(self, item):
        if item in ('font', 'pen', 'fm'):
            val = getattr(self, '_'+item)
            if not val:
                val = getattr(self, 'make_'+item)()
                setattr(self, '_'+item, val)
            return val

    # def make_font(self):
    #     pass

    def make_fm(self):
        return QFontMetrics(self.font)

    def make_pen(self):
        pass

    def get_size(self, item):
        return None, None

    def draw_line(self, painter, line, left, top, right, bottom, flags=Qt.AlignLeft | Qt.AlignTop):
        painter.drawText(QRectF(QPointF(left, top), QPointF(right, bottom)), flags, line)
        #painter.drawText(left, top + self.font_size, line)

    def make_font(self):
        font = QFont("Arial")
        font.setPixelSize(self.font_size)
        font.setBold(False)
        return font

    @property
    def debug(self):
        return self.kwargs.get('debug', False)


class PLayout(PBase):
    VERTICAL = 0
    HORIZONTAL = 1

    direction = None

    def __init__(self, *childs, **kwargs):
        super().__init__(**kwargs)
        self.childs = childs
        # self.calced_sizes = [None for _ in childs]
        # self.calced_size_situation = None

    def get_calced_sizes(self, item, size_tuple):
        # if getattr(item, 'calced_size_situation', None) != size_tuple:

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
            if w is not None:
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


class PHLayout(PLayout):
    direction = PLayout.HORIZONTAL

    def get_length_i_for_calc(self):
        return 0

    def _draw(self, painter: QPainter, delegate, item, rect_tuple: tuple):
        left, top, right, bottom = rect_tuple

        calced_sizes = self.get_calced_sizes(item, (right - left, bottom - top))

        l = left
        for i, child in enumerate(self.childs):
            w = calced_sizes[i]
            ml, mr = child.kwargs.get('margin_left', 0), child.kwargs.get('margin_right', 0)
            mt, _ = child.kwargs.get('margin_top', 0), child.kwargs.get('margin_bottom', 0)
            l += ml
            if w is not None:
                r = l + w
            else:
                r = right
            child.draw(painter, delegate, item, (l, top + mt, r, bottom))
            r += mr
            if r > l:
                l = r + 1
            if l >= right:
                break

    def get_size(self, item):
        max_h = None
        for child in self.childs:
            _, h = child.get_size(item)
            if h is None:
                max_h = None
                break
            else:
                if not max_h or h > max_h:
                    max_h = h
        return None, max_h


class PVLayout(PLayout):
    direction = PLayout.VERTICAL

    def get_length_i_for_calc(self):
        return 1

    def _draw(self, painter: QPainter, delegate, item, rect_tuple: tuple):
        left, top, right, bottom = rect_tuple

        calced_sizes = self.get_calced_sizes(item, (right - left, bottom - top))

        t = top
        for i, child in enumerate(self.childs):
            h = calced_sizes[i]
            ml, _ = child.kwargs.get('margin_left', 0), child.kwargs.get('margin_right', 0)
            mt, mb = child.kwargs.get('margin_top', 0), child.kwargs.get('margin_bottom', 0)
            t += mt
            if h is not None:
                b = t + h
            else:
                b = bottom
            child.draw(painter, delegate, item, (left + ml, t, right, b))
            b += mb
            if b > t:
                t = b + 1
            if t >= bottom:
                break

    def get_size(self, item):
        max_w = None
        for child in self.childs:
            w, _ = child.get_size(item)
            if w is None:
                max_w = None
                break
            else:
                if not max_w or w > max_w:
                    max_w = w
        return max_w, None


class PChatImage(PBase):

    def get_size(self, item):
        return 50, 50

    def _draw(self, painter: QPainter, delegate, item, rect_tuple: tuple):
        w, h = self.get_size(item)
        self.drawRound(painter, delegate, item, rect_tuple[0], rect_tuple[1], w, h)
        self.drawImage(painter, delegate, item, rect_tuple[0], rect_tuple[1], w, h)
        self.drawStatus(painter, delegate, item, rect_tuple[0], rect_tuple[1], w, h)

    def drawRound(self, painter, delegate, item, left, top, w, h):
        round_color = self.color_from_item(item)
        if round_color:
            iw = w  # self.image_width()
            ir = iw / 2
            painter.setPen(round_color)
            painter.setBrush(round_color)
            painter.drawEllipse(QPointF(left + ir, top + ir), ir, ir)

    def drawImage(self, painter, delegate, item, left, top, w, h):
        _image_left_add = 0
        iw = w  # self.image_width()

        pixmap = item.getPixmap()
        is_simple_icon = False
        if type(pixmap) == str:
            pixmap = pixmap_from_file(pixmap, iw, iw)
            is_simple_icon = True
        if pixmap:
            pixmap: QPixmap
            if is_simple_icon:
                pixmap = pixmap.scaledToWidth(32 / 50 * iw, Qt.SmoothTransformation)
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
            elif type(status_color) == tuple:
                status_color = QColor(*status_color)

            pen.setWidth(2)
            pen.setColor(QColor(255, 255, 255))

            painter.setPen(pen)
            painter.setBrush(status_color)
            painter.drawEllipse(QPointF(left + 45, top + 40), 6, 6)

    def color_from_item(self, item):
        item_color = item.getColor()
        if item_color:

            if type(item_color) == str:
                item_color = color_from_hex(item_color)

            return item_color


class PChatDownLine(PBase):

    def get_size(self, item):
        return None, 1

    def _draw(self, painter: QPainter, delegate, item, rect_tuple: tuple):
        left, top, right, bottom = rect_tuple
        painter.setPen(QColor(220, 220, 220))
        painter.drawLine(left, bottom, right, bottom)


class PStretch(PBase):

    def get_size(self, item):
        return None, None


class PLogin(PBase):

    def get_size(self, item):
        r = self.fm.boundingRect("W")
        return None, r.height()

    def _draw(self, painter: QPainter, delegate, item, rect_tuple: tuple):
        left, top, right, bottom = rect_tuple

        painter.setPen(self.pen)
        painter.setFont(self.font)

        _name = item.getName()
        _nick = item.getNick()

        brect = painter.boundingRect(QRectF(left, 0, 9999, 50), _name)
        if brect.right() >= right:
            max_len = int((right - left) / 10)
            _name = _name[:max_len] + "..."

        #painter.drawText(left, top + self.font_size, _name)
        self.draw_line(painter, _name, left, top, right, bottom)

        # if _nick and _nick != _name:
        #     draw_badges(painter, _nick, left+34, top+55, font_pixel_size=10,
        #                 bcolor='#7777cc', plus=False, factor=0.6)

    def make_pen(self):
        pen = QPen()
        pen.setWidth(1)
        pen.setColor(QColor(30, 30, 30))
        return pen

    def make_font(self):
        font = super().make_font()
        font.setBold(True)
        return font

    @property
    def font_size(self):
        return 14


class PLastMessage(PBase):

    def get_size(self, item):
        r = self.fm.boundingRect("W")
        return None, r.height()

    def _draw(self, painter: QPainter, delegate, item, rect_tuple: tuple):
        left, top, right, bottom = rect_tuple

        pen = QPen()
        pen.setWidth(1)
        pen.setColor(delegate.message_text_color())
        painter.setPen(pen)

        font = self.font
        painter.setFont(font)

        second_text = item.getSecondText()

        _text = second_text.replace("\n", " ").replace("\r", "").replace("\t", " ")
        while "  " in _text:
            _text = _text.replace("  ", " ")

        brect = self.fm.boundingRect(left, 0, 9999, 50, Qt.Horizontal, _text)
        if brect.right() > right - 10:  # FIXME
            max_len = int((right - left) / 6)
            _text = _text[:max_len] + "..."

        #painter.drawText(left, top, _text)
        self.draw_line(painter, _text, left, top, right, bottom)

    def make_font(self):
        font = super().make_font()
        font.setBold(False)
        return font

    @property
    def font_size(self):
        return 12


class PLastTime(PBase):

    def get_size(self, item):
        time_string = item.getTimeString()
        if time_string:
            r = self.fm.boundingRect(time_string)
            w, h = r.width()+4, r.height()
        else:
            w = h = 0
        return w, h

    def _draw(self, painter: QPainter, delegate, item, rect_tuple: tuple):
        left, top, right, bottom = rect_tuple

        time_string = item.getTimeString()
        if time_string:
            pen = QPen()
            pen.setWidth(1)
            pen.setColor(delegate.message_text_color())
            painter.setPen(pen)

            painter.setFont(self.font)
            #painter.drawText(left, top + self.font_size, time_string)
            self.draw_line(painter, time_string, left, top, right, bottom, Qt.AlignRight | Qt.AlignTop)

    @property
    def font_size(self):
        return 12


class PChatLayout(PHLayout):

    def _draw(self, painter: QPainter, delegate, item, rect_tuple: tuple):
        left, top, right, bottom = rect_tuple

        background_color = None

        if delegate.is_on_item(item):
            background_color = QColor(245, 245, 245)

        if item.isSelectedItem():
            if background_color:
                background_color = QColor(235, 235, 235)
            else:
                background_color = QColor(240, 240, 240)

        if background_color:
            painter.fillRect(QRectF(QPointF(left, top), QPointF(right, bottom)), background_color)

        super()._draw(painter, delegate, item, rect_tuple)
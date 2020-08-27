from os.path import exists, join, expanduser
from copy import copy
from sys import argv

from PyQt5.QtGui import QFontMetrics, QPainter, QColor, QIcon, QFont, QPen
from PyQt5.QtCore import Qt, QRectF, QPointF, QSize, QRect, QPoint

from ..core.draw import icon_from_file
from bp_chat.core.local_db_files_map import getDownloadsFilePath, LocalDbFilesMap
from ...logic.data import QuoteInfo


WORD_TYPE_SIMPLE = 0
WORD_TYPE_LINK = 1

LINE_TYPE_BASE = -1
LINE_TYPE_FILE = 100


class MessageDrawer:

    LINK_COLOR = '#0078d7'
    LINK_COLOR_HOVER = '#3397d7'
    RESEND_COLOR = '#3078ab'
    TEXT_COLOR = '#333333'
    TEXT_WHITE_COLOR = '#FFFFFF'
    INFO_COLOR = '#808080'

    rect = (0, 0, 0, 0)

    def __init__(self, message, font, text, delegate):
        self.message = message
        self._font = font
        message.drawer = self
        self.delegate = delegate

        self.metrics = QFontMetrics(font)
        w_rect = self.metrics.boundingRect(0, 0, 9999, 9999, Qt.Horizontal, 'w')
        self.line_height = w_rect.height() * 0.88
        self.w_width = w_rect.width()
        if self.w_width > 5:
            self.w_width = 5

        self.lines = [
            self.split_line(line) #[WordDrawer(w.strip(), self) for w in line.split(' ')]
            for line in text.split('\n')
        ]
        
        self.quote_lines = []
        self.quote_file = None
        if hasattr(message.message, 'quote') and message.message.quote:
            _quote_text = message.message.get_quote_text()
            if not _quote_text:
                _quote_text = ''

            self.quote_lines = [
                self.split_line(line) for line in _quote_text.split('\n')
            ]

            quote_filename = message.message.getFileName()
            quote_file = message.message.getFile()
            quote_file_size = message.message.getFileSize()
            if quote_file and quote_file not in (0, '0'):
                self.quote_file = QuoteFile(quote_file, quote_filename, quote_file_size, self)

        self.file_line = None
        if hasattr(message.message, 'file'):
            file = message.message.file
            has_file = file is not None and len(file) > 1
            if has_file:
                filename = message.message.getFileName()
                self.file_line = FileLine(message.message.getFile(), filename, message.message.getFileSize(), self)

        self.links = set()

    @property
    def font(self):
        return self._font

    def split_line(self, line):
        _words = line.split(' ')
        _new_words = []
        for i, w in enumerate(_words):
            if type(w) == int:
                continue
            w = w.strip()
            w, link = self.get_link_from_word(w)
            if link:
                w_drawer = LinkWordDrawer(w, self, link)
            else:
                w_drawer = WordDrawer(w, self)

            _new_words.append(w_drawer)

        return _new_words

    def prepare_line(self, line, left_top_right, space_width, line_height, line_cls=None):
        if line_cls == None:
            line_cls = WordsLine

        left, top_now, right = left_top_right
        left_now = left - space_width

        _words = line.split(' ') if type(line) == str else line

        last_i = i = 0
        to_new_lines = []

        for i, w_drawer in enumerate(_words):
            if type(w_drawer) == int:
                continue

            left_now += space_width
            left_now_0 = left_now
            r_right = left_now + w_drawer.width

            if r_right > right:
                to_new_lines.append(line_cls(_words[last_i:i]))
                last_i = i
                left_now = left + w_drawer.width
                top_now += line_height
            else:
                left_now = r_right

            if w_drawer.word_type == WORD_TYPE_LINK:

                y_start = top_now
                y = top_now + line_height
                x = left_now_0
                x_end = r_right

                w_drawer.rect = (x, y_start, x_end, y)
                w_drawer.rect_local = True
                self.links.add(w_drawer)

        if len(to_new_lines) == 0:
            to_new_lines.append(line_cls(_words))
            top_now += line_height
        elif last_i <= i:
            to_new_lines.append(line_cls(_words[last_i:]))
            top_now += line_height

        #print(to_new_lines)

        return to_new_lines, top_now

    @staticmethod
    def get_link_from_word(word):
        link = None
        if word.startswith('https://') or word.startswith('http://'):
            link = word
        elif word.startswith('#'):
            if word.startswith('#INPUT_CALL:'):
                _from = word[len('#INPUT_CALL:'):]
                link = word
                word = 'Входящий звонок от ' + _from
        return word, link


class LineBase:
    line_type = LINE_TYPE_BASE
    first_word_left = 0


class WordsLine(LineBase, list):

    _line_height = 14
    font_height = 14

    def __init__(self, lst, line_height=14):
        list.__init__(self, lst)

        self._line_height = line_height

    @property
    def line_height(self):
        return self._line_height

    def draw_line(self, mes_drawer, painter, left_top_right_bottom, sel_start, sel_end):

        left, top_now, right, bottom_now = left_top_right_bottom
        left += self.first_word_left

        space_width = mes_drawer.w_width
        line_height = self.line_height
        line_start = top_now - line_height
        line_end = top_now

        select_start_in_this_line = select_end_in_this_line = select_start_upper = select_end_lower = False
        if sel_start and sel_end:
            select_start_in_this_line = line_start <= sel_start[1] <= line_end
            select_end_in_this_line = line_start <= sel_end[1] <= line_end
            select_start_upper = (sel_start[1] <= line_start or sel_end[1] <= line_start)
            select_end_lower = (sel_end[1] >= line_end or sel_start[1] >= line_end)

        selected_words = []

        temp_pen = painter.pen()

        # ----
        # pen_changed = True
        # painter.setPen(QPen(QColor("#ff0000")))
        # painter.drawRect(QRect(QPoint(left, line_start), QPoint(right, line_end)))
        # if sel_start and sel_end:
        #     painter.setPen(QPen(QColor("#007700")))
        #     painter.drawRect(QRect(QPoint(sel_start[0], sel_start[1]), QPoint(sel_end[0], sel_end[1])))
        # painter.setPen(QPen(QColor("#000000")))
        # ----

        w_left = left
        for w in self:

            a_left = w_left
            a_right = a_left

            pen_changed = False
            need_draw_line_under = False
            if w.word_type == WORD_TYPE_LINK:
                pen_changed = True
                x, y_start, x_end, y = w.rect
                if mes_drawer.delegate._mouse_on_link == w:
                    need_draw_line_under = True
                    painter.setPen(QPen(QColor(mes_drawer.LINK_COLOR_HOVER)))
                else:
                    painter.setPen(QPen(QColor(mes_drawer.LINK_COLOR)))

            selected_aa = []
            for a, a_w in zip(w, w.widths):
                a_right = a_left + a_w

                if sel_start and sel_end:
                    aw2 = a_w / 2
                    if (
                            (select_start_upper and select_end_lower) or
                            (select_start_in_this_line and select_end_in_this_line and
                                ((a_left+aw2 >= sel_start[0] and a_right-aw2 <= sel_end[0]) or
                                (a_left+aw2 >= sel_end[0] and a_right-aw2 <= sel_start[0])))
                            or (select_start_in_this_line and select_end_lower and (a_left+aw2) >= sel_start[0])
                            or (select_start_upper and select_end_in_this_line and (a_right-aw2) <= sel_end[0])
                    ):
                        painter.fillRect(QRectF(QPointF(a_left, top_now - self.font_height+2), QPointF(a_right, top_now+2)),
                                         QColor("#cccccc"))
                        selected_aa.append(a)

                a_left += a_w


            if len(selected_aa) > 0:
                selected_words.append(''.join(selected_aa))

            painter.drawText(w_left, top_now, w)
            if need_draw_line_under:
                #painter.drawLine(x, y + 3, x_end, y + 3)
                painter.drawLine(w_left, top_now+2, a_right, top_now+2)

            w_left = a_right + space_width

            if pen_changed:
                painter.setPen(temp_pen)

        if len(selected_words) > 0:
            return ' '.join(selected_words) # FIXME



class FileLine(LineBase):

    # first_word_left = 5

    line_type = LINE_TYPE_FILE
    _line_height_tuple = None

    def __init__(self, file_uuid, filename, filesize, message_drawer):
        self.file_uuid = file_uuid
        self.filename = filename
        self.filesize = filesize
        self.message_drawer = message_drawer

    def __str__(self):
        return '[FILE:{}]'.format( self.filename)

    def __repr__(self):
        return self.__str__()

    @property
    def line_height(self):
        if self._line_height_tuple == None or not self._line_height_tuple[2]:
            self._line_height_tuple = self.get_size_base()
        return self._line_height_tuple[1]

    def get_size(self, font_height=12):
        return self.get_size_base()[:2]

    def get_size_base(self):
        _fullpath = getDownloadsFilePath(self.filename, self.file_uuid)
        file_exists = exists(_fullpath)

        pixmap_w, pixmap_h, calced = 30, 30, False

        if file_exists:
            calced = True
            _lower_fullpath = _fullpath.lower()
            if _lower_fullpath.endswith('.jpg') or _lower_fullpath.endswith('.png'):

                icon = LocalDbFilesMap.images.get(self.file_uuid, None)
                if not icon:
                    icon = QIcon(_fullpath)
                    LocalDbFilesMap.images[self.file_uuid] = icon

                sizes = icon.availableSizes()
                if sizes and len(sizes) > 0:
                    sz = sizes[0]
                    _w, _h = sz.width(), sz.height()
                    if _h > 100:
                        _h = 100
                        dh = _h / 100.0
                        _w = int(round(_w / dh))

                    if _w > 200:
                        _w = 200
                        dw = _w / 200
                        _h = int(round(_h / dw))

                    isz = icon.actualSize(QSize(_w, _h))
                    if isz.width() > 0 and isz.height() > 0:
                        pixmap_w, pixmap_h = isz.width(), isz.height()

        return pixmap_w, pixmap_h, calced

    def draw_line(self, mes_drawer, painter, left_top_right_bottom, sel_start, sel_end):

        left, top_now, right, bottom_now = left_top_right_bottom

        _fullpath = getDownloadsFilePath(self.filename, self.file_uuid)
        file_exists = exists(_fullpath)

        pixmap_w, pixmap_h = self.get_size()

        if file_exists:
            _lower_fullpath = _fullpath.lower()
            if _lower_fullpath.endswith('.jpg') or _lower_fullpath.endswith('.png'):
                icon = QIcon(_fullpath)
                #self.images[_file_uuid] = icon
                isz = icon.actualSize(QSize(pixmap_w, pixmap_h))
                if isz.width() > 0 and isz.height() > 0:
                    pixmap_w, pixmap_h = isz.width(), isz.height()
                    #print(f'[ DRAW size ] {pixmap_w} {pixmap_h}')
                else:
                    icon = icon_from_file("file")
            else:
                icon = icon_from_file("file")

        else:
            icon = icon_from_file("download_file")

        text_rect = QRect(QPoint(left+self.first_word_left, top_now-14), QPoint(right, bottom_now-14))

        file_pixmap = icon.pixmap(QSize(pixmap_w, pixmap_h))
        self._draw_file(mes_drawer, painter, file_pixmap, text_rect, pixmap_w, pixmap_h, mouse_pos=mes_drawer.delegate._mouse_pos)

    def _draw_file(self, mes_drawer, painter, file_pixmap, text_rect, pixmap_w, pixmap_h, mouse_pos):

        left = text_rect.left()
        right = text_rect.right()
        #infoRect = QRect(0, 0, 200, 100)

        file_p = QPointF(left, text_rect.top())
        image = file_pixmap.toImage()

        temp_pen = painter.pen()
        temp_font = painter.font()

        if 'P_DEBUG' in argv:
            painter.setPen(QColor(mes_drawer.RESEND_COLOR))
            painter.drawRect(text_rect)
            painter.drawRect(QRectF(file_p, QPointF(left+image.width(), text_rect.top()+image.height())))

        painter.drawImage(file_p, image)

        font = QFont()
        font.setBold(True)
        painter.setFont(font)
        fm = QFontMetrics(font)
        font_h = fm.height()

        file_name = self.filename
        fileNameRect = painter.boundingRect(
            QRect(QPoint(left + pixmap_w + 10, text_rect.top()), QPoint(right - 10, text_rect.bottom())),
            Qt.TextWordWrap, file_name
        )

        rect = (left, text_rect.top(), fileNameRect.right(), max([fileNameRect.bottom(), text_rect.top() + pixmap_h]))
        # is_mouse_in = (
        #     rect[0] <= mouse_pos[0] <= rect[2] and
        #     rect[1] <= mouse_pos[1] <= rect[3]
        # )
        self.rect = rect
        mes_drawer.links.add(self)
        #print('>> mes_drawer >> links: {}'.format(mes_drawer.links))

        if mes_drawer.delegate._mouse_on_link == self:
            painter.setPen(QPen(QColor(mes_drawer.LINK_COLOR_HOVER)))
            #mes_drawer.delegate.listView._cursor_need_cross = True
        else:
            painter.setPen(QPen(QColor(mes_drawer.RESEND_COLOR)))

        painter.drawText(fileNameRect, Qt.TextWordWrap, file_name)

        # file size
        painter.setPen(QPen(QColor(mes_drawer.RESEND_COLOR)))
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        file_size = self.filesize
        fileSizeRect = painter.boundingRect(
            QRect(QPoint(fileNameRect.left(), fileNameRect.bottom()), QPoint(fileNameRect.right(), text_rect.bottom())),
            Qt.TextWordWrap, file_size)
        painter.drawText(fileSizeRect, Qt.TextWordWrap, file_size)

        painter.setFont(temp_font)
        painter.setPen(temp_pen)


class QuoteDrawAdd:

    def draw_left_line(self, painter: QPainter, left, top, bottom, minus_line_height=None):
        temp_pen = painter.pen()

        painter.setPen(QPen(QColor(self.message_drawer.RESEND_COLOR), 3))
        #left = left - self.first_word_left
        if minus_line_height == None:
            lh = self.line_height
        else:
            lh = minus_line_height
        painter.drawLine(left, top-lh+1, left, bottom-lh-1)

        painter.setPen(temp_pen)


class QuoteAuthor(LineBase, QuoteDrawAdd):

    first_word_left = 10
    # line_height = 8
    margin_first_top = 4

    def __init__(self, quote: QuoteInfo, message_drawer):
        self.quote = quote
        self.message_drawer = message_drawer

    @property
    def first_word_left(self):
        sender = self.quote.getSenderName()
        if not sender or len(sender) == 0:
            return 0
        return 10

    @property
    def line_height(self):
        sender = self.quote.getSenderName()
        h = 14
        if not sender or len(sender) == 0:
            h = 0
        #print('>>> [ QUOUTE sender ] {} = {}'.format(sender, h))
        return h

    def get_size(self, font_height):
        sender = self.quote.getSenderName()
        if not sender or len(sender) == 0:
            return 0, 0
        return 0, font_height

    def draw_line(self, mes_drawer, painter, left_top_right_bottom, sel_start, sel_end):
        left, top, right, bottom = left_top_right_bottom

        temp_pen = painter.pen()
        temp_font = painter.font()

        self.draw_left_line(painter, left, top, bottom)

        painter.setPen(QPen(QColor(self.message_drawer.RESEND_COLOR)))
        font = QFont()
        font.setBold(True)
        painter.setFont(font)
        fm = QFontMetrics(font)
        font_h = fm.height()
        font_height = - self.line_height + font_h

        painter.drawText(left + self.first_word_left, top + font_height - 2, self.quote.getSenderName())

        painter.setPen(temp_pen)
        painter.setFont(temp_font)


class QuoteLine(WordsLine, QuoteDrawAdd):

    first_word_left = 10
    _line_height = 14
    is_last_quote_line = False

    def __init__(self, lst, quote: QuoteInfo, message_drawer):
        self.quote = quote
        self.message_drawer = message_drawer
        super().__init__(lst)
        self.pen = QPen(QColor(message_drawer.INFO_COLOR))

    @property
    def line_height(self):
        return (10 + self._line_height) if self.is_last_quote_line else self._line_height

    def draw_line(self, mes_drawer, painter, left_top_right_bottom, sel_start, sel_end):
        left, top, right, bottom = left_top_right_bottom
        temp_pen = painter.pen()

        self.draw_left_line(painter, left, top, bottom)

        painter.setPen(self.pen)

        ret = super().draw_line(mes_drawer, painter, left_top_right_bottom, sel_start, sel_end)

        painter.setPen(temp_pen)
        return ret


class QuoteFile(FileLine, QuoteDrawAdd):

    first_word_left = 10

    def draw_line(self, mes_drawer, painter, left_top_right_bottom, sel_start, sel_end):
        left, top, right, bottom = left_top_right_bottom

        self.draw_left_line(painter, left, top, bottom, minus_line_height=14)

        super().draw_line(mes_drawer, painter, left_top_right_bottom, sel_start, sel_end)


class WordDrawer(str):

    rect_local = False

    metrics = None

    @staticmethod
    def __new__(cls, word: str, message_drawer: MessageDrawer, word_type: int = WORD_TYPE_SIMPLE):
        obj = str.__new__(cls, word)
        obj.message_drawer = message_drawer
        obj.word_type = word_type

        if not WordDrawer.metrics:
            font = QFont("Arial")
            font.setPixelSize(14)
            font.setBold(False)
            WordDrawer.metrics = QFontMetrics(font)

        metrics = WordDrawer.metrics

        w = 0
        ws = []
        for a in obj:
            a_w = metrics.boundingRect(0, 0, 9999, 9999, Qt.Horizontal, a).width()
            w += a_w
            ws.append(a_w)
        obj.width = w
        obj.widths = tuple(ws)
        return obj


class LinkWordDrawer(WordDrawer):

    text_color = '#ff0000'

    @staticmethod
    def __new__(cls, word: str, message_drawer, url: str):
        obj = WordDrawer.__new__(cls, word=word, message_drawer=message_drawer, word_type=WORD_TYPE_LINK)
        obj.url = url
        return obj

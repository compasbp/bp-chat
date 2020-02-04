from os.path import exists, join, expanduser

from PyQt5.QtGui import QFontMetrics, QPainter, QColor, QIcon, QFont, QPen
from PyQt5.QtCore import Qt, QRectF, QPointF, QSize, QRect, QPoint

from ..core.draw import icon_from_file
from bp_chat.core.files_map import getDownloadsFilePath, FilesMap

WORD_TYPE_SIMPLE = 0
LINE_TYPE_BASE = -1
LINE_TYPE_FILE = 100


class MessageDrawer:

    LINK_COLOR = '#0078d7'
    LINK_COLOR_HOVER = '#3397d7'
    RESEND_COLOR = '#3078ab'
    TEXT_COLOR = '#333333'
    TEXT_WHITE_COLOR = '#FFFFFF'
    INFO_COLOR = '#808080'

    def __init__(self, message, font, text):
        self.message = message
        self._font = font
        message.drawer = self

        self.metrics = QFontMetrics(font)
        w_rect = self.metrics.boundingRect(0, 0, 9999, 9999, Qt.Horizontal, 'w')
        self.line_height = w_rect.height()
        self.w_width = w_rect.width()
        if self.w_width > 5:
            self.w_width = 5

        lines = text.split('\n')
        self.lines = [
            [WordDrawer(w.strip(), self) for w in line.split(' ')] for line in lines
        ]

    @property
    def font(self):
        return self._font


class LineBase:
    line_type = LINE_TYPE_BASE


class WordsLine(LineBase, list):

    def __init__(self, lst, line_height=14):
        list.__init__(self, lst)

        self.line_height = line_height

    # def get_size(self, font_height):
    #     return (0, font_height)

    def draw_line(self, mes_drawer, painter, left_top_right_bottom, sel_start, sel_end):

        left, top_now, right, bottom_now = left_top_right_bottom

        space_width = mes_drawer.w_width
        line_height = self.line_height
        line_start = top_now - line_height
        line_end = top_now

        select_start_in_this_line = select_end_in_this_line = select_start_upper = select_end_lower = False
        if sel_start and sel_end:
            select_start_in_this_line = line_start <= sel_start[1] <= line_end
            select_end_in_this_line = line_start <= sel_end[1] <= line_end
            select_start_upper = sel_start[1] <= line_start
            select_end_lower = sel_end[1] >= line_end

        w_left = left
        for w in self:

            a_left = w_left
            a_right = a_left
            for a in w:
                r = mes_drawer.metrics.boundingRect(0, 0, 9999, 9999, Qt.Horizontal,
                                                a)  # painter.boundingRect(QRectF(0, 0, 500, 500), a)

                a_right = a_left + r.width()

                if sel_start and sel_end:
                    if (
                            (select_start_upper and select_end_lower) or
                            (select_start_in_this_line and select_end_in_this_line and a_left >= sel_start[
                                0] and a_right <= sel_end[0]) or
                            (select_start_in_this_line and not select_end_in_this_line and a_left >= sel_start[0]) or
                            (not select_start_in_this_line and select_end_in_this_line and a_right <= sel_end[0])
                    ):
                        painter.fillRect(QRectF(QPointF(a_left, top_now - line_height), QPointF(a_right, top_now)),
                                         QColor("#cccccc"))

                a_left += r.width()

            #max_width = max(max_width, a_left)

            painter.drawText(w_left, top_now, w)
            w_left = a_right + space_width



class FileLine(LineBase):

    # first_word_left = 5

    line_type = LINE_TYPE_FILE
    _line_height = None

    def __init__(self, file_uuid, filename, filesize, message_drawer):
        self.file_uuid = file_uuid
        self.filename = filename
        self.filesize = filesize
        self.message_drawer = message_drawer

    @property
    def line_height(self):
        if self._line_height == None:
            self._line_height = self.get_size()[1]
        return self._line_height

    def get_size(self, font_height=12):
        _fullpath = getDownloadsFilePath(self.filename, self.file_uuid)
        file_exists = exists(_fullpath)

        pixmap_w, pixmap_h = 30, 30

        if file_exists:
            _lower_fullpath = _fullpath.lower()
            if _lower_fullpath.endswith('.jpg') or _lower_fullpath.endswith('.png'):

                icon = FilesMap.images.get(self.file_uuid, None)
                if not icon:
                    icon = QIcon(_fullpath)
                    FilesMap.images[self.file_uuid] = icon

                sizes = icon.availableSizes()
                if sizes and len(sizes) > 0:
                    # self.images[_file_uuid] = icon
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

        return pixmap_w, pixmap_h

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

        text_rect = QRect(QPoint(left, top_now), QPoint(right, bottom_now))

        file_pixmap = icon.pixmap(QSize(pixmap_w, pixmap_h))
        self._draw_file(painter, file_pixmap, text_rect, pixmap_w, pixmap_h, mouse_pos=(-1, -1))

    def _draw_file(self, painter, file_pixmap, text_rect, pixmap_w, pixmap_h, mouse_pos):

        left = text_rect.left()
        right = text_rect.right()
        #infoRect = QRect(0, 0, 200, 100)

        painter.drawImage(QPointF(left, text_rect.top()), file_pixmap.toImage())

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
        is_mouse_in = (
            rect[0] <= mouse_pos[0] <= rect[2] and
            rect[1] <= mouse_pos[1] <= rect[3]
        )
        #self.message_drawer.links.add((self, rect))

        if is_mouse_in:
            painter.setPen(QPen(QColor(self.message_drawer.LINK_COLOR_HOVER)))
            self.message_drawer.delegate.listView.cursor_need_cross = True
        else:
            painter.setPen(QPen(QColor(self.message_drawer.RESEND_COLOR)))

        painter.drawText(fileNameRect, Qt.TextWordWrap, file_name)

        # file size
        painter.setPen(QPen(QColor(self.message_drawer.RESEND_COLOR)))
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        file_size = self.filesize
        fileSizeRect = painter.boundingRect(
            QRect(QPoint(fileNameRect.left(), fileNameRect.bottom()), QPoint(fileNameRect.right(), text_rect.bottom())),
            Qt.TextWordWrap, file_size)
        painter.drawText(fileSizeRect, Qt.TextWordWrap, file_size)


class WordDrawer(str):

    @staticmethod
    def __new__(cls, word: str, message_drawer: MessageDrawer, word_type: int = WORD_TYPE_SIMPLE):
        obj = str.__new__(cls, word)
        obj.message_drawer = message_drawer
        obj.word_type = word_type
        w = 0
        for a in obj:
            a_w = message_drawer.metrics.boundingRect(0, 0, 9999, 9999, Qt.Horizontal, a).width()
            w += a_w
        obj.width = w
        return obj



from PyQt5.QtWidgets import QItemDelegate, QListView, QFrame, QStyledItemDelegate
from PyQt5.QtGui import QColor, QPainter, QFont, QFontMetrics
from PyQt5.QtCore import (QAbstractListModel, QSize, QPointF, QRectF, pyqtSignal, QEvent, Qt, QItemSelection,
                          QItemSelectionModel)

from threading import Timer

from bp_chat.gui.core.draw import draw_badges, get_round_mask, color_from_hex
from .funcs import item_from_object


class ListView(QListView):

    _selected_callback = None

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def set_selected_callback(self, callback):
        self._selected_callback = callback

    def selectionChanged(self, selectedSelection, deselectedSelection):
        if self._selected_callback:
            self._selected_callback([ind.data() for ind in selectedSelection.indexes()])

    def resizeEvent(self, e):
        ret = super().resizeEvent(e)
        self.model().reset_model()
        return ret



class ListDelegate(QItemDelegate):

    round_mask = None
    _mouse_pos = (-1, -1)

    def __init__(self, listView, list_model):
        super().__init__(listView)

        self.listView = listView
        self.list_model = list_model

        listView.setItemDelegate(self)
        listView.installEventFilter(self)

    def get_round_mask(self, size=(50, 50), to_size=(50, 50)):
        _w, _h = size
        w, h = to_size
        if not self.round_mask or _w != 50*5 or _h != 50*5:
            map = get_round_mask(size=(_w, _h), to_size=to_size, border_radius=None)

            if _w == _h == 50*5:
                self.round_mask = map
            else:
                return map

        return self.round_mask

    def paint(self, painter, option, index):

        left, top, right, bottom = self.prepare_base_left_top_right_bottom(option)

        painter.setRenderHint(QPainter.Antialiasing)

        item = self.list_model.data(index)

        self.fillRect(painter, item, index.row(), option)

        self.drawRound(painter, item, left, top)

        self.drawImage(painter, item, left, top)

        self.drawStatus(painter, item, left, top)

        self.drawMessage(painter, item, (left, top, right, bottom))

        time_string_left = -1
        time_string = self.list_model.getItemTimeString(item)
        if time_string:

            time_string_left = right - 6*len(time_string)-10 + self.list_model.getRightAdd()
            painter.drawText(time_string_left, top + 28, time_string)

        pen = painter.pen()

        pen.setWidth(1)
        pen.setColor(QColor(30, 30, 30))
        painter.setPen(pen)

        font = painter.font()
        font.setPixelSize(14)
        font.setBold(True)
        painter.setFont(font)

        _name = self.list_model.getItemName(item)
        _name_left = left + 50 + 16

        if time_string_left >= 10:
            brect = painter.boundingRect(QRectF(_name_left, 0, 9999, 50), _name)
            if brect.right() >= time_string_left:
                max_len = int((time_string_left - _name_left) / 10)
                _name = _name[:max_len] + "..."

        painter.drawText(_name_left, top + 28, _name)

        # draw badges
        badges_count = self.list_model.getItemBadgesCount(item)
        if badges_count > 0:
            draw_badges(painter, badges_count, left + 39 + 8, top + 20 + 8 - 6, muted=self.list_model.getMuted(item))

        painter.setPen(QColor(220, 220, 220))

        painter.drawLine(left + 50 + 16, bottom - 1, right-left, bottom - 1) # top + 68

        main_draw_results = (time_string_left, self.list_model.getRightAdd())

        self.list_model.customDraw(painter, item, (left, top, right, bottom), main_draw_results)

    def prepare_base_left_top_right_bottom(self, option):
        return option.rect.left(), option.rect.top(), option.rect.right(), option.rect.bottom()

    def fillRect(self, painter, item, index_row, option):
        background_color = QColor(255, 255, 255)

        selected = False
        # current_item_id = self.list_model.getCurrentItemIndex()
        # if item and current_item_id != -1 and current_item_id == index_row:
        #     selected = True
        rows = [ind.row() for ind in self.listView.selectedIndexes()]

        selected = index_row in rows

        if selected:
            background_color = QColor(235, 235, 235)

        # selected_item_id = self.list_model.getSelectedItemIndex()
        # if selected_item_id != -1 and selected_item_id == index_row:
        #     background_color = QColor(240, 240, 240)

        if item and self.list_model.selected_item == item:
            background_color = QColor(240, 240, 240)

        painter.fillRect(option.rect.adjusted(1, 1, -1, -1), background_color)  # Qt.SolidPattern)

    def drawMessage(self, painter: QPainter, item, left_top_right_bottom):
        left, top, right, bottom = left_top_right_bottom

        painter.setPen(QColor(150, 150, 150))

        font = self.prepareMessageFont()
        painter.setFont(font)

        second_text = self.list_model.getItemSecondText(item)
        if second_text:

            message_left, message_top = self.prepareMessageStartPosition(left, top)

            left_top_right_bottom = (message_left, message_top, right, bottom)

            _text = self.prepareMessageText(second_text, left_top_right_bottom)

            self.drawMessageText(painter, _text, left_top_right_bottom)

    def prepareMessageStartPosition(self, left, top):
        message_left = left + 50 + 16
        message_top = top + 48
        return message_left, message_top

    def prepareMessageFont(self):
        font = QFont("Arial")
        font.setPixelSize(12)
        font.setBold(False)
        return font

    def prepareMessageText(self, second_text, left_top_right_bottom):
        left, top, right, bottom = left_top_right_bottom

        font = self.prepareMessageFont()
        metrics = QFontMetrics(font)

        _text = second_text.replace("\n", " ")
        while "  " in _text:
            _text = _text.replace("  ", " ")

        brect = metrics.boundingRect(left, 0, 9999, 50, Qt.Horizontal, _text)
        if brect.right() + self.list_model.getRightAdd() > right - 10:  # FIXME
            max_len = int((right - left) / 6)
            _text = _text[:max_len] + "..."

        return _text

    def drawMessageText(self, painter, text, left_top_right_bottom):
        left, top, right, bottom = left_top_right_bottom
        painter.drawText(left, top, text)

    def drawRound(self, painter, item, left, top):
        round_color = self.color_from_item(item)
        if round_color:
            painter.setPen(round_color)
            painter.setBrush(round_color)
            painter.drawEllipse(QPointF(left + 25 + 8, top + 25 + 8), 25, 25)

    def drawImage(self, painter, item, left, top):
        _image_left_add = 0
        pixmap = self.list_model.getItemPixmap(item)
        if pixmap:
            painter.drawImage(QPointF(left + 8 + _image_left_add, top + 8), pixmap.toImage())

    def drawStatus(self, painter, item, left, top):
        pen = painter.pen()

        status_color = self.list_model.getItemStatusColor(item)
        if status_color:

            if type(status_color) == str:
                status_color = color_from_hex(status_color)

            pen.setWidth(2)
            pen.setColor(QColor(255, 255, 255))

            painter.setPen(pen)
            painter.setBrush(status_color)
            painter.drawEllipse(QPointF(left + 45 + 8, top + 40 + 8), 6, 6)

    def sizeHint(self, option, index):
        item = self.list_model.data(index)
        width = self.listView.width()
        h = self.list_model.getItemHeight(item, option)
        return QSize(width, h)

    def color_from_item(self, item):
        item_color = self.list_model.getItemColor(item)
        if item_color:

            if type(item_color) == str: # FIXME !!!
                status_color = color_from_hex(item_color)

            return status_color

    def eventFilter(self, obj, event):

        if event.type() in (QEvent.MouseMove, QEvent.HoverMove):
            self._mouse_pos = event.pos().x(), event.pos().y()

        return super().eventFilter(obj, event)


class ListModel(QAbstractListModel):

    _need_reset_signal = pyqtSignal()
    _need_reset_timer = None

    _items_dict: {str: object}
    _keys_list: []
    _model_item = None

    def __init__(self, listView, items_dict=None, list_delegate_cls=ListDelegate):
        super().__init__()

        if not items_dict:
            items_dict = {}
        self.items_dict = items_dict

        self.delegate = list_delegate_cls(listView, self)

        self.selected_item = None
        self.filter = None
        self.sorter = None
        self._auto_update_items = True

        listView.setModel(self)

        self._need_reset_signal.connect(self._reset_model_do)

    @property
    def items_dict(self):
        return self._items_dict

    @items_dict.setter
    def items_dict(self, val):
        self._items_dict = val
        self._keys_list = sorted(list(val.keys()))

    @property
    def model_item(self):
        return self._model_item

    @model_item.setter
    def model_item(self, val):
        self._model_item = val

    def set_auto_update_items(self, value):
        self._auto_update_items = value

    def set_filter(self, filter):
        self.filter = filter

    def set_sorter(self, sorter):
        self.sorter = sorter

    def set_selected_item(self, item):
        self.selected_item = item

    def rowCount(self, parent=None):
        return len(self.items_dict)

    def columnCount(self, parent):
        return 1

    def data(self, index, role=None):
        key = self._keys_list[index.row()]
        item_pre = self.items_dict[key]
        item = item_from_object(item_pre, self.model_item)
        return item

    # def updateDraws(self):
    #     if self._updateDraws__Timer:
    #         self._updateDraws__Timer.cancel()
    #     self._updateDraws__Timer = Timer(0.1, self._updateDraws__Start)
    #     self._updateDraws__Timer.start()
    #
    # def _updateDraws__Start(self):
    #     self._updateDraws__Signal.emit()
    #
    # def _updateDraws__Slot(self):
    #     self.prepareItems()
    #     self.beginResetModel()
    #     self.endResetModel()
    #
    # def prepareItems(self):
    #     if not self._auto_update_items:
    #         return
    #
    #     self.items_list = self._items_list
    #     if self.filter:
    #         self.items_list = self.filter(self.items_list)
    #     if self.sorter:
    #         self.items_list = self.sorter(self.items_list)

    def getCurrentItemIndex(self):
        return -1

    def getSelectedItemIndex(self):
        return -1

    def getItemName(self, item):
        return item.getName()

    def getItemSecondText(self, item):
        return item.getSecondText()

    def getItemTimeString(self, item):
        return item.getTimeString()

    def getItemPixmap(self, item):
        return item.getPixmap()

    def getItemBadgesCount(self, item):
        return item.getBadgesCount()

    def getMuted(self, item):
        return False

    def getItemColor(self, item):
        return item.getColor()

    def getItemStatusColor(self, item):
        return item.getStatusColor()

    def getItemHeight(self, item, option):
        return 70

    def getRightAdd(self):
        return 0

    def customDraw(self, painter, item, left_top_right_bottom, main_draw_results):
        pass

    def reset_model(self):
        if self._need_reset_timer:
            return
        self._need_reset_timer = Timer(0.1, self._reset_model)
        self._need_reset_timer.start()

    def _reset_model(self):
        self._need_reset_signal.emit()
        self._need_reset_timer = None

    def _reset_model_do(self):
        temp_indx = self.delegate.listView.selectedIndexes()

        self.beginResetModel()
        self.endResetModel()

        item_selection = QItemSelection()
        for i in temp_indx:
            item_selection.select(i, i)

        self.delegate.listView.selectionModel().select(item_selection, QItemSelectionModel.Select)


class MessagesListDelegate(ListDelegate):

    def prepare_base_left_top_right_bottom(self, option):
        ret = super().prepare_base_left_top_right_bottom(option)
        return ret

    def prepareMessageText(self, second_text, left_top_right_bottom):
        left, top, right, bottom = left_top_right_bottom

        font = self.prepareMessageFont()
        metrics = QFontMetrics(font)

        w_rect = metrics.boundingRect(0, 0, 9999, 9999, Qt.Horizontal, 'w')
        line_height = w_rect.height()
        space_width = w_rect.width()

        top_now = top - line_height
        left_now = left - space_width

        lines = second_text.split('\n')
        new_lines = []

        for line in lines:
            top_now += line_height
            words = line.split(' ')

            last_i = i = 0
            to_new_lines = []
            for i, w in enumerate(words):
                left_now += space_width
                r = metrics.boundingRect(left_now, top_now, 9999, 9999, Qt.Horizontal, w)

                if r.right() > right:
                    to_new_lines.append(words[last_i:i])
                    last_i = i
                    left_now = left
                    top_now += line_height
                else:
                    left_now = r.right()

            if len(to_new_lines) == 0:
                to_new_lines.append(words)
            elif last_i < i:
                to_new_lines.append(words[last_i:])

            new_lines += to_new_lines

        return line_height, new_lines

    def drawMessageText(self, painter, line_height_and_lines, left_top_right_bottom):
        left, top, right, bottom = left_top_right_bottom
        line_height, lines = line_height_and_lines

        top_now = top
        for words in lines:
            painter.drawText(left, top_now, ' '.join(words))
            top_now += line_height

    def sizeHint(self, option, index):
        ret = super().sizeHint(option, index)
        return ret


class MessagesListModel(ListModel):

    def __init__(self, listView):
        super().__init__(listView, list_delegate_cls=MessagesListDelegate)

    def getItemHeight(self, item, option):
        right = option.rect.right()
        message_left, message_top = self.delegate.prepareMessageStartPosition(0, 0)

        left_top_right_bottom = message_left, message_top, right, 99999

        second_text = self.getItemSecondText(item)
        if second_text:
            line_height, new_lines = self.delegate.prepareMessageText(second_text, left_top_right_bottom)
            h = (len(new_lines)) * line_height
            h_top = message_top - option.rect.top()
            h += h_top
            return h

        return 70


class ListModelItem:

    def getName(self):
        raise NotImplementedError

    def getSecondText(self):
        return None

    def getTimeString(self):
        return None

    def getPixmap(self):
        return None

    def getBadgesCount(self):
        return 0

    def getColor(self):
        return None

    def getStatusColor(self):
        return None



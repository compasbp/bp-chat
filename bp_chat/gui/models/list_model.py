

from PyQt5.QtWidgets import QItemDelegate, QListView
from PyQt5.QtGui import QColor, QPainter, QFont
from PyQt5.QtCore import QAbstractListModel, QSize, QPointF, QRectF, pyqtSignal, QEvent

from threading import Timer

from bp_chat.gui.core.draw import draw_badges, get_round_mask, color_from_hex


class ListView(QListView):

    _selected_callback = None


    def setSelectedCallback(self, callback):
        self._selected_callback = callback

    def selectionChanged(self, selectedSelection, deselectedSelection):
        if self._selected_callback:
            self._selected_callback()


class ListModel(QAbstractListModel):

    _updateDraws__Signal = pyqtSignal()
    _updateDraws__Timer = None

    def __init__(self, listView, items_list):
        super().__init__()

        self._items_list = items_list
        self.items_list = items_list

        self.delegate = ListDelegate(listView, self)

        self.selected_item = None
        self.filter = None
        self.sorter = None
        self._auto_update_items = True

        listView.setModel(self)

        self._updateDraws__Signal.connect(self._updateDraws__Slot)

    def set_auto_update_items(self, value):
        self._auto_update_items = value

    def set_filter(self, filter):
        self.filter = filter

    def set_sorter(self, sorter):
        self.sorter = sorter

    def set_selected_item(self, item):
        self.selected_item = item

    def rowCount(self, parent=None):
        return len(self.items_list)

    def columnCount(self, parent):
        return 1

    def data(self, index, role=None):
        return self.items_list[index.row()]

    def updateDraws(self):
        if self._updateDraws__Timer:
            self._updateDraws__Timer.cancel()
        self._updateDraws__Timer = Timer(0.1, self._updateDraws__Start)
        self._updateDraws__Timer.start()

    def _updateDraws__Start(self):
        self._updateDraws__Signal.emit()

    def _updateDraws__Slot(self):
        self.prepareItems()
        self.beginResetModel()
        self.endResetModel()

    def prepareItems(self):
        if not self._auto_update_items:
            return

        self.items_list = self._items_list
        if self.filter:
            self.items_list = self.filter(self.items_list)
        if self.sorter:
            self.items_list = self.sorter(self.items_list)

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

    def getItemHeight(self, item, width=280):
        return 70

    def getRightAdd(self):
        return 0

    def customDraw(self, painter, item, left_top_right_bottom, main_draw_results):
        pass


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

        left, top, right, bottom = option.rect.left(), option.rect.top(), option.rect.right(), option.rect.bottom()

        painter.setRenderHint(QPainter.Antialiasing)

        item = self.list_model.items_list[index.row()]

        self.fillRect(painter, item, index.row(), option)

        self.drawRound(painter, item, left, top)

        self.drawImage(painter, item, left, top)

        self.drawStatus(painter, item, left, top)

        painter.setPen(QColor(150, 150, 150))

        font = QFont("Arial") #font = painter.font()
        font.setPixelSize(12)

        font.setBold(False)
        painter.setFont(font)

        time_string_left = -1
        second_text = self.list_model.getItemSecondText(item)
        if second_text:
            message_left = left + 50 + 16
            message_top = top + 48

            _text = second_text.replace("\n", " ")
            while "  " in _text:
                _text = _text.replace("  ", " ")

            brect = painter.boundingRect(QRectF(message_left, 0, 9999, 50), _text)
            if brect.right() + self.list_model.getRightAdd() > right - 10: # FIXME
                max_len = int((right - message_left) / 6)
                _text = _text[:max_len] + "..."

            painter.drawText(message_left, message_top, _text)

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
        painter.drawLine(left + 50 + 16, top + 68, right-left, top + 68)

        main_draw_results = (time_string_left, self.list_model.getRightAdd())

        self.list_model.customDraw(painter, item, (left, top, right, bottom), main_draw_results)


    def fillRect(self, painter, item, index_row, option):
        background_color = QColor(255, 255, 255)

        selected = False
        current_item_id = self.list_model.getCurrentItemIndex()
        if item and current_item_id != -1 and current_item_id == index_row:
            selected = True

        if selected:
            background_color = QColor(235, 235, 235)

        # selected_item_id = self.list_model.getSelectedItemIndex()
        # if selected_item_id != -1 and selected_item_id == index_row:
        #     background_color = QColor(240, 240, 240)

        if item and self.list_model.selected_item == item:
            background_color = QColor(240, 240, 240)

        painter.fillRect(option.rect.adjusted(1, 1, -1, -1), background_color)  # Qt.SolidPattern)

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
        item = self.list_model.items_list[index.row()]
        h = self.list_model.getItemHeight(item, width=280)
        return QSize(280, h)

    def color_from_item(self, item):
        item_color = self.list_model.getItemColor(item)
        if item_color:

            if type(item_color) == str:
                status_color = color_from_hex(item_color)

            return status_color

    def eventFilter(self, obj, event):
        #print(event.type())
        if event.type() in (QEvent.MouseMove, QEvent.HoverMove):
            self._mouse_pos = event.pos().x(), event.pos().y()

        return super().eventFilter(obj, event)


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



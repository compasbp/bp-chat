
from PyQt5.QtWidgets import (QItemDelegate, QListView, QFrame, QStyledItemDelegate, QMenu, QScrollBar,
                             QAbstractItemView, QApplication, QScrollBar, QGraphicsOpacityEffect)
from PyQt5.QtGui import (QColor, QPainter, QFont, QFontMetrics, QPixmap, QCursor, QPen, QGuiApplication, QFontMetricsF)
from PyQt5.QtCore import (QAbstractListModel, QSize, QPointF, QPoint, QRectF, QRect, pyqtSignal, QEvent, Qt, QItemSelection,
                          QItemSelectionModel, QPropertyAnimation, QEasingCurve)

from threading import Timer
from copy import copy
from datetime import datetime
from sys import platform

from bp_chat.gui.core.draw import draw_badges, get_round_mask, color_from_hex
from .funcs import item_from_object
from .drawers import MessageDrawer, WordsLine, FileLine
from ..core.draw import pixmap_from_file, icon_from_file, IconDrawer


class ListView(QListView):

    _selected_callback = None
    _current_selection = None
    _scroll_animation = None
    _scroll_show_animation = None
    _scroll_ignore_value = False
    _scroll_before_load_state = None

    def __init__(self, parent=None):
        super().__init__(parent)

        self._after_scroll_range_change_actions = []

        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll: QScrollBar = self.verticalScrollBar()
        scroll.setPageStep(10)
        scroll.setSingleStep(10)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setMouseTracking(True)

        self._custom_selection = CustomSelection()

        self.scroll = QScrollBar(self)
        #self.scroll.setWindowOpacity(0)
        self.scroll.valueChanged.connect(self.on_scroll_changed)
        scroll.rangeChanged.connect(self.on_scroll_range_changed)

    def scroll_to_bottom(self):
        if self._scroll_to_bottom not in self._after_scroll_range_change_actions:
            self._after_scroll_range_change_actions.append(self._scroll_to_bottom)

        self.model().reset_model(action=self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        maximum = self.verticalScrollBar().maximum()
        print('_scroll_to_bottom', maximum, self.scroll.maximum())
        self.scroll.setValue(self.scroll.maximum())

    def scroll_to_state(self, maximum):
        self._scroll_before_load_state = maximum
        if self._scroll_to_bottom not in self._after_scroll_range_change_actions:
            self._after_scroll_range_change_actions.append(self._scroll_to_state)
        #self.model().reset_model(lambda: self._scroll_to_state(value, maximum))

    def _scroll_to_state(self):
        maximum = self._scroll_before_load_state
        if maximum == None:
            return
        self._scroll_before_load_state = None
        scroll_maximum = self.scroll.maximum()
        new_value = scroll_maximum - maximum
        print('[ _scroll_to_state ] {}/{} -> {}/{}'.format(0, maximum, new_value, scroll_maximum))
        # if maximum > scroll_maximum:
        #     self.scroll.setMaximum(maximum)
        if self.scroll.maximum() > maximum:
            print('  -> ', new_value)
            self.scroll.setValue(new_value)

    def showEvent(self, *args, **kwargs):
        ret = super().showEvent(*args, **kwargs)
        self.animate_scroll_show(show=False, time=100)
        return ret

    def set_selected_callback(self, callback):
        self._selected_callback = callback

    def selectionChanged(self, selectedSelection, deselectedSelection):
        _new_selection = [ind.data() for ind in selectedSelection.indexes()]
        if self._current_selection == _new_selection:
            return
        self._current_selection = _new_selection
        if self._selected_callback:
            self._selected_callback(_new_selection)
        self.model().reset_model()

    def on_scroll_changed(self, value):
        if self._scroll_ignore_value:
            return
        scroll: QScrollBar = self.verticalScrollBar()
        scroll.setValue(value)

    def on_scroll_range_changed(self, _min, _max):
        print('on_scroll_range_changed', _min, _max, self.verticalScrollBar().maximum())
        self.scroll.setRange(_min, _max)
        self._after_scroll_range_change_actions, actions = [], self._after_scroll_range_change_actions
        for action in actions:
            func = getattr(self, action) if type(action) == str else action
            func()

    def resizeEvent(self, e):
        ret = super().resizeEvent(e)
        self.scroll.move(self.width() - 10, 0)
        self.scroll.resize(10, self.height())
        self.model().reset_model()
        return ret

    def mousePressEvent(self, e):
        delegate = self.itemDelegate()

        if e.button() == Qt.LeftButton:
            self._custom_selection.active = True
            self._custom_selection.start = (e.pos().x(), e.pos().y())
            self._custom_selection.end = None

            delegate.on_custom_selection_changed(self._custom_selection)

        return super().mousePressEvent(e)

    def mouseMoveEvent(self, e):

        delegate = self.itemDelegate()
        pos = (e.pos().x(), e.pos().y())

        if self._custom_selection.active:
            self._custom_selection.end = pos

            delegate.on_custom_selection_changed(self._custom_selection)

        delegate.on_mouse_pos_changed(pos)

        return super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):

        self._custom_selection.active = False

        if e.button() == Qt.RightButton:
            self.open_menu_for_selected_item(e.globalPos())

        return super().mouseReleaseEvent(e)

    def enterEvent(self, e):

        delegate = self.itemDelegate()
        pos = (e.pos().x(), e.pos().y())

        delegate.on_mouse_pos_changed(pos)

        self.animate_scroll_show(show=True)

        return super().enterEvent(e)

    def leaveEvent(self, e):

        delegate = self.itemDelegate()
        delegate.on_mouse_pos_changed((-1, -1))

        self.animate_scroll_show(show=False)

        return super().leaveEvent(e)

    def wheelEvent(self, e):
        #return super().wheelEvent(e)
        dy = e.pixelDelta().y()
        dya = e.angleDelta().y()
        scroll: QScrollBar = self.verticalScrollBar()
        #print(dy, dya, scroll.value(), scroll.maximum())
        e.ignore()

        last_value = scroll.value()
        new_value = last_value - int(round(dya / 1))

        self.change_scroll_animated(new_value)

        #scroll.setValue(new_value)
        #return super().wheelEvent(e)

    def change_scroll_animated(self, new_value):

        scroll: QScrollBar = self.verticalScrollBar()

        last_value = scroll.value()
        if new_value < 0:
            new_value = 0
        elif new_value > scroll.maximum():
            new_value = scroll.maximum()

        if platform == 'darwin':
            self.scroll.setValue(new_value)
            return

        if self._scroll_animation:
            self._scroll_animation.stop()
            last_value = scroll.value() #self._scroll_animation._next

        self._scroll_ignore_value = True
        self.scroll.setValue(new_value)
        self._scroll_ignore_value = False

        self._scroll_animation = QPropertyAnimation(scroll, b"value")
        self._scroll_animation.setDuration(100)
        self._scroll_animation.setStartValue(last_value)
        self._scroll_animation.setEndValue(new_value)
        self._scroll_animation._next = new_value

        self._scroll_animation.start()


    def animate_scroll_show(self, show=True, time=500):
        if self._scroll_show_animation:
            self._scroll_show_animation.stop()
            self._scroll_show_animation.deleteLater()
        # self._scroll_show_animation = QPropertyAnimation(self.scroll, b"windowOpacity")
        # self._scroll_show_animation.setDuration(100)
        # self._scroll_show_animation.setStartValue(1)
        # self._scroll_show_animation.setEndValue(0)
        # self._scroll_show_animation.start()

        start, end = (0.0, 1.0) if show else (1.0, 0.0)

        fade_effect = QGraphicsOpacityEffect(self.scroll)
        self.scroll.setGraphicsEffect(fade_effect)
        self._scroll_show_animation = animation = QPropertyAnimation(fade_effect, b"opacity")
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.setDuration(time)
        animation.setStartValue(start)
        animation.setEndValue(end)
        animation.start()#QPropertyAnimation.DeleteWhenStopped)

    def clear_selection(self):
        self._current_selection = None
        self.clearSelection()

    def open_menu_for_selected_item(self, global_pos):
        chat = self._current_selection[0] if self._current_selection else None
        menu = self.model().make_menu(chat) if chat else None
        if menu:
            menu.exec_(global_pos)



class ListDelegate(QItemDelegate):

    round_mask = None
    _mouse_pos = (-1, -1)
    _mouse_on_item = None
    _mouse_on_image = None
    _mouse_on_name = None

    def __init__(self, listView, list_model):
        super().__init__(listView)

        self.listView = listView
        self.list_model = list_model

        listView.setItemDelegate(self)
        listView.installEventFilter(self)

        self.icon_drawer = IconDrawer(listView)

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

        need_draw_image_and_title = self.need_draw_image_and_title(item)

        self.fillRect(painter, item, index.row(), option)

        if need_draw_image_and_title:
            self.drawRound(painter, item, left, top)
            self.drawImage(painter, item, left, top)
            self.drawStatus(painter, item, left, top)

        self.drawMessage(painter, item, (left, top, right, bottom))

        if type(item.item) == LoadMessagesButton:
            return

        painter.setPen(QColor(150, 150, 150))

        time_string_left = -1
        time_string = self.list_model.getItemTimeString(item)
        if time_string:
            font = self.prepareTimeFont()
            painter.setFont(font)
            time_string_left = right - 6*len(time_string)-10 + self.list_model.getRightAdd()
            painter.drawText(time_string_left, self.time_top(top, bottom), time_string)

        pen, font = self.prepare_pen_and_font_for_name(painter, item)
        painter.setPen(pen)
        painter.setFont(font)

        if need_draw_image_and_title:
            self.draw_name(painter, item, left, top, time_string_left)

        # draw badges
        badges_count = self.list_model.getItemBadgesCount(item)
        if badges_count > 0:
            draw_badges(painter, badges_count, left + 39 + 8, top + 20 + 8 - 6, muted=self.list_model.getMuted(item))

        painter.setPen(QColor(220, 220, 220))

        self.draw_down_line(painter, left, bottom, right)

        main_draw_results = (time_string_left, self.list_model.getRightAdd())

        self.list_model.customDraw(painter, item, (left, top, right, bottom), main_draw_results)

    def draw_name(self, painter, item, left, top, time_string_left):
        _name = self.list_model.getItemName(item)
        _name_left = left + self._name_left_add()

        if time_string_left >= 10:
            brect = painter.boundingRect(QRectF(_name_left, 0, 9999, 50), _name)
            if brect.right() >= time_string_left:
                max_len = int((time_string_left - _name_left) / 10)
                _name = _name[:max_len] + "..."

        painter.drawText(_name_left, self.title_top(top), _name)

    def title_top(self, top):
        return self.message_top(top) - 20

    def prepare_pen_and_font_for_name(self, painter: QPainter, item):
        pen = painter.pen()

        pen.setWidth(1)
        pen.setColor(QColor(30, 30, 30))

        font = self.prepare_font_for_name()

        return pen, font

    def prepare_font_for_name(self):
        # font = painter.font()
        font = QFont("Arial")
        font.setPixelSize(14)
        font.setBold(True)
        return font

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

        painter.setPen(self.message_text_color())

        font = self.prepareMessageFont()
        painter.setFont(font)

        second_text = self.list_model.getItemSecondText(item)
        if second_text:

            message_left, message_top = self.prepareMessageStartPosition(left, top)

            left_top_right_bottom = (message_left, message_top, right, bottom)

            _text = self.prepareMessageText(item, second_text, left_top_right_bottom)

            self.drawMessageText(painter, _text, left_top_right_bottom, item)

    def message_font_size(self):
        return 12

    def time_font_size(self):
        return 11

    def message_text_color(self):
        return QColor(150, 150, 150)

    def prepareMessageStartPosition(self, left, top):
        message_left = left + 50 + 16
        message_top = self.message_top(top)
        return message_left, message_top

    def message_top(self, top):
        return top + 48

    def image_width(self):
        return 50

    def image_left_add(self):
        return 0

    def need_draw_image_and_title(self, item):
        return True

    def time_top(self, top, bottom):
        return top + 28

    def draw_down_line(self, painter, left, bottom, right):
        painter.drawLine(left + 50 + 16, bottom - 1, right - left, bottom - 1)  # top + 68

    def _name_left_add(self):
        return 50 + 16

    def prepareMessageFont(self):
        font = QFont("Arial")
        font.setPixelSize(self.message_font_size())
        font.setBold(False)
        return font

    def prepareTimeFont(self):
        font = QFont("Arial")
        font.setPixelSize(self.time_font_size())
        font.setBold(False)
        return font

    def prepareMessageText(self, item, second_text, left_top_right_bottom):
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

    def drawMessageText(self, painter, text, left_top_right_bottom, item):
        left, top, right, bottom = left_top_right_bottom
        painter.drawText(left, top, text)

    def drawRound(self, painter, item, left, top):
        round_color = self.color_from_item(item)
        if round_color:
            iw = self.image_width()
            ir = iw / 2
            painter.setPen(round_color)
            painter.setBrush(round_color)
            painter.drawEllipse(QPointF(left + ir + 8 + self.image_left_add(), top + ir + 8), ir, ir)

    def drawImage(self, painter, item, left, top):
        _image_left_add = 0
        iw = self.image_width()

        pixmap = self.list_model.getItemPixmap(item)
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
            #painter.drawImage(QPointF(left + 8 + _image_left_add, top + 8), pixmap.toImage())
            self.icon_drawer.draw_pixmap(painter, pixmap, (left + 8 + self.image_left_add(), top + 8), size=(iw, iw),
                    under_mouse=self._is_under_mouse(item),
                    icon_size=(iw, iw), actual_size=actual_size, alpha=1.0)

    def _is_under_mouse(self, item):
        return self._is_mouse_on_image(item)

    def _is_mouse_on_image(self, item):
        return self._mouse_on_image == item

    def _is_mouse_on_name(self, item):
        return self._mouse_on_name == item

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

            if type(item_color) == str:
                item_color = color_from_hex(item_color)

            return item_color

    def eventFilter(self, obj, event):

        # if event.type() in (QEvent.MouseMove, QEvent.HoverMove):
        #     self._mouse_pos = pos = (event.pos().x(), event.pos().y())
        #     self.on_mouse_pos_changed(pos)
        #
        # elif event.type() == QEvent.Leave:
        #     self._mouse_pos = pos = (-1, -1)
        #     self.on_mouse_pos_changed(pos)

        return super().eventFilter(obj, event)

    def on_custom_selection_changed(self, custom_selection):
        pass

    def on_mouse_pos_changed(self, pos):
        changed = False
        self._mouse_pos = pos

        index = self.listView.indexAt(QPoint(*pos))
        item = None
        if index:
            item = index.data()

        if item and type(item.item) != LoadMessagesButton:
            if self.change_value('_mouse_on_item', item):
                changed = True

            rect = self.listView.visualRect(index)

            if self.calc_and_change_is_on_pos('_mouse_on_image', pos, item,
                                              QRect(QPoint(rect.left() + 8, rect.top() + 8),
                                                    QPoint(rect.left() + 58, rect.top() + 58))):
                changed = True

            _name = item.getName()
            font = self.prepare_font_for_name()
            fm = QFontMetricsF(font)
            br = fm.boundingRect(_name)
            _left = rect.left() + self._name_left_add()
            _right = min(rect.right(), _left + br.width())

            title_top = self.title_top(rect.top()) - 16

            if self.calc_and_change_is_on_pos('_mouse_on_name', pos, item,
                                              QRect(QPoint(_left-10, title_top #rect.top() + 16
                                                           ),
                                                    QPoint(_right, title_top + 14 #rect.top() + 16 + 14
                                                           ))):
                changed = True

        else:
            for name in ('item', 'image', 'name'):
                if self.change_value('_mouse_on_'+name, None):
                    changed = True

        if changed:
            self.update_cursor()
            self.list_model.reset_model()

    def update_cursor(self):
        to_shape = Qt.ArrowCursor
        if self._mouse_on_image or self._mouse_on_name:
            to_shape = Qt.PointingHandCursor

        listView: QListView = self.listView
        cursor: QCursor = listView.cursor()
        if cursor.shape() != to_shape:
            cursor.setShape(to_shape)
            listView.setCursor(cursor)

    def change_value(self, name, value):
        if getattr(self, name) != value:
            setattr(self, name, value)
            return True
        return False

    def calc_and_change_is_on_pos(self, name, pos, item, check_rect):
        new_value = None
        if check_rect.top() <= pos[1] <= check_rect.bottom() and check_rect.left() <= pos[0] <= check_rect.right():
            new_value = item
        return self.change_value(name, new_value)


class ListModel(QAbstractListModel):

    _need_reset_signal = pyqtSignal(object)
    _need_reset_timer = None

    _items_dict: {str: object}
    _keys_list: []
    _model_item = None

    def __init__(self, listView, items_dict=None, list_delegate_cls=ListDelegate):
        super().__init__()

        self._reset_actions = []

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
        # self._items_dict = val
        # self._keys_list = sorted(list(val.keys()))

        val, self._keys_list = self.set_items_dict(val)
        self._items_dict = val

        last = None
        for k in self._keys_list:
            # if type(k) != int:
            #     print(k, type(k))
            if k < 0:
                continue
            m = val[k]
            m.last_item = last
            last = m

    def set_items_dict(self, val):
        return val, sorted(list(val.keys()))

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

    def make_menu(self, item):
        pass

    def reset_model(self, action='_reset_model_do_action'):
        if action not in self._reset_actions:
            self._reset_actions.append(action)

        if self._need_reset_timer:
            return
        self._need_reset_timer = Timer(0.1, self._reset_model)
        self._need_reset_timer.start()

    def _reset_model(self):
        actions, self._reset_actions = self._reset_actions, []
        for a in actions:
            self._need_reset_signal.emit(a)
            self._need_reset_timer = None

    def _reset_model_do(self, action):
        #actions, self._reset_actions = copy(self._reset_actions), []
        func = getattr(self, action) if type(action) == str else action
        func()

    def _reset_model_do_action(self):
        #print('_reset_model_do_action', datetime.now())
        temp_indx = self.delegate.listView.selectedIndexes()

        self.beginResetModel()
        self.endResetModel()

        item_selection = QItemSelection()
        for i in temp_indx:
            item_selection.select(i, i)

        self.delegate.listView.selectionModel().select(item_selection, QItemSelectionModel.Select)


class ChatsModel(ListModel):

    def make_menu(self, chat_item):
        chat = chat_item.chat

        menu = QMenu(self.delegate.listView)
        createGroupAction = menu.addAction(icon_from_file("create_group"), "Create group")
        createGroupAction.triggered.connect(self.on_create_group_action)
        is_admin = False #ChatApi.instance().is_admin

        if chat.type == chat.PRIVATE:
            profileAction = menu.addAction(icon_from_file("profile"), "Edit user" if is_admin else "Show profile")
            profileAction.triggered.connect(lambda: self.onProfileAction(chat.user.id))
        elif chat.type == chat.GROUP:
            profileAction = menu.addAction(icon_from_file("edit"), "Edit group")
            profileAction.triggered.connect(lambda: self.onChatEdit(chat))

            deleteAction = menu.addAction(icon_from_file("delete"), "Remove group")
            deleteAction.triggered.connect(lambda: self.onRemoveEdit(chat))
        # elif chat.is_live():
        #     if chat.is_mine():
        #         finAction = menu.addAction(icon_from_file("finish_dialog"), "Finish live chat")
        #         finAction.triggered.connect(lambda: self.onFinishLiveChat(chat))
        #     else:
        #         takeAction = menu.addAction(icon_from_file("take"), "Take live chat")
        #         takeAction.triggered.connect(lambda: self.onTakeLiveChat(chat))
        #     if is_admin:
        #         profileAction = menu.addAction(icon_from_file("profile"), "Edit guest")
        #         profileAction.triggered.connect(lambda: self.onProfileAction(user_id=None, live_chat_id=chat.chat_id))

        updateAction = menu.addAction(icon_from_file("refresh"), "Refresh chats")
        updateAction.triggered.connect(self.on_refresh_action)

        #chat_api = ChatApi.instance()
        chat_muted = False #chat_api.is_chat_muted(chat.chat_id)
        chat_pinned = False #chat_api.is_chat_pinned(chat.chat_id)

        mute_name = 'unmute' if chat_muted else 'mute'
        muteAction = menu.addAction(icon_from_file(mute_name), mute_name[:1].upper() + mute_name[1:])
        muteAction.triggered.connect(lambda: self.onMuteAction(mute_name, chat.id))

        filtered_by_last_readed = [False]

        def is_filtered_by_last_readed(boo):
            filtered_by_last_readed[0] = boo

        badges_count = 0 #chat.get_badges_count(is_filtered_by_last_readed=is_filtered_by_last_readed)
        if badges_count > 0:
            markAllReadAction = menu.addAction(icon_from_file("all_read"), "Mark all read")
            markAllReadAction.triggered.connect(lambda: self.onMarkAllReadAction(chat))
        elif filtered_by_last_readed[0]:
            unmarkAllReadAction = menu.addAction(icon_from_file("remove_all_read"), "Unmark all read")
            unmarkAllReadAction.triggered.connect(lambda: self.onMarkAllReadAction(chat, unmark=True))

        if chat_pinned:
            delFromPinned_Action = menu.addAction(icon_from_file("pinned"), "Remove from pinned")
            delFromPinned_Action.triggered.connect(lambda: self.onDelFromPinned_Action(chat))
        else:
            addToPinned_Action = menu.addAction(icon_from_file("pin"), "Add to pinned")
            addToPinned_Action.triggered.connect(lambda: self.onAddToPinned_Action(chat))

        return menu

    def on_refresh_action(self):
        pass

    def on_create_group_action(self):
        pass


class MessagesListDelegate(ListDelegate):

    # def prepareMessageStartPosition(self, left, top):
    #     message_left = left + 50 + 16
    #     message_top = top + 38
    #     return message_left, message_top
    last_load_min_message_id = None

    def prepare_base_left_top_right_bottom(self, option):
        ret = super().prepare_base_left_top_right_bottom(option)
        return ret

    def image_width(self):
        return 38

    def image_left_add(self):
        return 12

    def message_top(self, top):
        return top + 38

    def get_min_message_id(self):
        lst = [k for k in self.list_model._keys_list if k >= 0]
        return min(lst) if len(lst) > 0 else None

    def prepareMessageText(self, item, second_text, left_top_right_bottom):
        left, top, right, bottom = left_top_right_bottom
        right -= 10

        drawer = getattr(item, 'drawer', None)
        if not drawer:
            drawer = MessageDrawer(item, self.prepareMessageFont(), second_text)

        if isinstance(item.message, LoadMessagesButton):
            return 30, item.message

        # font = drawer.font
        # metrics = QFontMetrics(font)

        #w_rect = metrics.boundingRect(0, 0, 9999, 9999, Qt.Horizontal, 'w')
        line_height = drawer.line_height #w_rect.height()
        space_width = drawer.w_width #w_rect.width()
        message_height = 0

        top_now = top #- line_height
        left_now = left - space_width

        lines = drawer.lines #second_text.split('\n')
        new_lines = []
        max_width = 0

        for line in lines:
            # top_now += line_height

            last_i = i = 0
            to_new_lines = []
            for i, w_drawer in enumerate(line):
                left_now += space_width
                r_right = left_now + w_drawer.width

                if r_right > right:
                    max_width = max(max_width, left_now-space_width)
                    to_new_lines.append(WordsLine(line[last_i:i]))
                    last_i = i
                    left_now = left + w_drawer.width
                    top_now += line_height
                else:
                    left_now = r_right

            if len(to_new_lines) == 0:
                to_new_lines.append(WordsLine(line))
                top_now += line_height
            elif last_i < i:
                to_new_lines.append(WordsLine(line[last_i:]))
                top_now += line_height

            new_lines += to_new_lines

        message_height = (len(new_lines)) * line_height

        file = item.message.file
        has_file = file is not None and len(file) > 1
        if has_file:
            filename = item.message.getFileName()
            file_line = FileLine(item.message.getFile(), filename, item.message.getFileSize(), drawer)
            message_height += file_line.line_height

            new_lines.insert(0, file_line)
            if second_text == filename: # FIXME
                new_lines = new_lines[:1]

        return message_height, new_lines

    def drawMessageText(self, painter, line_height_and_lines, left_top_right_bottom, item):
        left, top, right, bottom = left_top_right_bottom
        right -= 10
        line_height, lines = line_height_and_lines

        custom_selection: CustomSelection = self.listView._custom_selection
        sel_start = custom_selection.start
        sel_end = custom_selection.end
        if sel_start and sel_end and sel_start[1] > sel_end[1]:
            sel_start, sel_end = sel_end, sel_start

        drawer: MessageDrawer = item.drawer

        top_now = top
        if hasattr(lines, 'draw'):
            lines.draw(painter, left_top_right_bottom)

            if type(lines) == LoadMessagesButton:
                min_message_id = self.get_min_message_id()
                if self.last_load_min_message_id != min_message_id:
                    val, maximum = self.listView.verticalScrollBar().value(), self.listView.verticalScrollBar().maximum()
                    #self.listView.scroll.setValue(50)
                    self.listView.scroll_to_state(maximum)
                    self.last_load_min_message_id = min_message_id
                    self.list_model.on_need_download_20(min_message_id)

        else:
            for words_line in lines:

                line_height = words_line.line_height
                bottom_now = top_now + line_height

                words_line.draw_line(drawer, painter, (left, top_now, right, bottom_now), sel_start, sel_end)

                top_now = bottom_now

    def need_draw_image_and_title(self, item):
        item = item.item
        if type(item) == LoadMessagesButton:
            return False
        if item.last_item and item.sender == item.last_item.sender:
            return False
        return True

    def draw_down_line(self, painter, left, bottom, right):
        pass

    def message_text_color(self):
        return QColor(50, 50, 50)

    def time_top(self, top, bottom):
        return bottom - 10

    def message_font_size(self):
        return 14

    def sizeHint(self, option, index):
        ret = super().sizeHint(option, index)
        return ret

    def on_custom_selection_changed(self, custom_selection):
        self.list_model.reset_model()

    def make_menu(self):
        pass

    def _is_under_mouse(self, item):
        return self._is_mouse_on_image(item) or self._is_mouse_on_name(item)

    def prepare_pen_and_font_for_name(self, painter: QPainter, item):
        pen, font = super().prepare_pen_and_font_for_name(painter, item)
        if self._is_mouse_on_name(item) or self._is_mouse_on_image(item):
            font.setUnderline(True)
        return pen, font


class MessagesListModel(ListModel):

    def __init__(self, listView):
        super().__init__(listView, list_delegate_cls=MessagesListDelegate)

    def on_need_download_20(self, min_message_id):
        pass

    def getItemHeight(self, item, option):
        right = option.rect.right()
        message_left, message_top = self.delegate.prepareMessageStartPosition(0, 0)

        left_top_right_bottom = message_left, message_top, right, 99999

        second_text = self.getItemSecondText(item)
        if second_text:
            message_height, new_lines = self.delegate.prepareMessageText(item, second_text, left_top_right_bottom)
            #h = (len(new_lines)) * line_height
            h_top = message_top - option.rect.top()
            h = message_height + h_top + 20
            return h

        return 70

    def set_items_dict(self, val):
        messages_dict = { int(k):v for k, v in val.items() }
        keys_list = sorted(list(messages_dict.keys()), key=lambda key: (messages_dict[key].datetime, key))

        if len(messages_dict) >= 20: # FIXME
            messages_dict.keys()
            messages_dict[-1] = LoadMessagesButton()
            keys_list.insert(0, -1)

        return messages_dict, keys_list


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


class CustomSelection:

    active = False
    start = None
    end = None

    def __str__(self):
        return "{} {} - {}".format("A" if self.active else "D", self.start, self.end)


class LoadMessagesButton:

    text = "Load more messages"

    def __init__(self, text=None):
        if text is not None:
            self.text = text

    def draw(self, painter, left_top_right_bottom):
        left, top, right, bottom = left_top_right_bottom
        left, top, right, bottom = left-28, top-14, right-20, bottom-14

        painter.drawText(QRect(QPoint(left, top), QPoint(right, bottom)), Qt.AlignCenter, self.text)
        painter.drawRect(left+11, top+4, right-left-22, bottom-top-8)

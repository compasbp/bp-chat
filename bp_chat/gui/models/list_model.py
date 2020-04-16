
from PyQt5.QtWidgets import (QItemDelegate, QListView, QFrame, QStyledItemDelegate, QMenu, QScrollBar,
                             QAbstractItemView, QApplication, QScrollBar, QGraphicsOpacityEffect)
from PyQt5.QtGui import (QColor, QPainter, QFont, QFontMetrics, QPixmap, QCursor, QPen, QGuiApplication, QFontMetricsF)
from PyQt5.QtCore import (QAbstractListModel, QSize, QPointF, QPoint, QRectF, QRect, pyqtSignal, QEvent, Qt, QItemSelection,
                          QItemSelectionModel, QPropertyAnimation, QEasingCurve, QPersistentModelIndex)

from threading import Timer
from copy import copy
from datetime import datetime
from os.path import exists
from sys import platform, argv

from bp_chat.gui.core.draw import draw_badges, get_round_mask, color_from_hex
from .funcs import item_from_object
from .drawers import (MessageDrawer, WordsLine, FileLine, QuoteAuthor, QuoteLine, QuoteFile, WORD_TYPE_LINK,
                      LINE_TYPE_FILE)
from ..core.draw import pixmap_from_file, icon_from_file, IconDrawer, draw_icon_from_file
from bp_chat.core.files_map import getDownloadsFilePath, FilesMap
from .element_parts import (PHLayout, PChatImage, PVLayout, PLogin, PLastMessage, PLastTime, PChatDownLine, PStretch,
                            PChatLayout, PMessageImage, PMessage, PMessageLayout, PMessageLogin, PChatPinned,
                            PChatMuted, PMessageDelivered)
from .funcs import V_SCROLL_SHOW
from ..core.widgets import InfoLabel


NEED_DRAW_PPARTS = True
P_DEBUG = 'P_DEBUG' in argv

def set_NEED_DRAW_PPARTS(val):
    global NEED_DRAW_PPARTS
    NEED_DRAW_PPARTS = val


def print_timeit(func):
    if 'timeit' in argv:
        def _new_func(*args, **kwargs):
            start = datetime.now()
            ret = func(*args, **kwargs)
            dt = datetime.now() - start
            print(dt)
            return ret
    else:
        _new_func = func
    return _new_func


class ListView(QListView):

    _selected_callback = None
    _scroll_ignore_value = False
    _scroll_animation = None
    _scroll_show_animation = None

    last_index_at = None
    _entered = False

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMouseTracking(True)

        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setStyleSheet(V_SCROLL_SHOW)

        scroll: QScrollBar = self.verticalScrollBar()
        #scroll.setPageStep(10)
        #scroll.setSingleStep(10)

        self.scroll = QScrollBar(self)
        # self.scroll.setWindowOpacity(0)
        self.scroll.valueChanged.connect(self.on_scroll_changed)
        scroll.rangeChanged.connect(self.on_scroll_range_changed)
        scroll.valueChanged.connect(self.on_scroll_changed_real)

    def set_selected_callback(self, callback):
        self._selected_callback = callback

    def on_scroll_changed(self, value):
        if self._scroll_ignore_value:
            return
        scroll: QScrollBar = self.verticalScrollBar()
        scroll.setValue(value)

    def on_scroll_changed_real(self, value):
        pass

    def wheelEvent(self, e):
        dy = e.pixelDelta().y()
        dya = e.angleDelta().y()
        scroll: QScrollBar = self.verticalScrollBar()
        e.ignore()

        last_value = scroll.value()
        new_value = last_value - int(round(dya / 1))

        self.change_scroll_animated(new_value)

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
            last_value = scroll.value()

        self._scroll_ignore_value = True
        self.scroll.setValue(new_value)
        self._scroll_ignore_value = False

        self._scroll_animation = QPropertyAnimation(scroll, b"value")
        self._scroll_animation.setDuration(100)
        self._scroll_animation.setStartValue(last_value)
        self._scroll_animation.setEndValue(new_value)

        self._scroll_animation.start()

        # self.move_custom_selection_for_scroll(new_value)

    def animate_scroll_show(self, show=True, time=500):
        if self._scroll_show_animation:
            self._scroll_show_animation.stop()
            self._scroll_show_animation.deleteLater()

        start, end = (0.0, 1.0) if show else (1.0, 0.0)

        fade_effect = QGraphicsOpacityEffect(self.scroll)
        self.scroll.setGraphicsEffect(fade_effect)
        self._scroll_show_animation = animation = QPropertyAnimation(fade_effect, b"opacity")
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.setDuration(time)
        animation.setStartValue(start)
        animation.setEndValue(end)
        animation.start()

    def on_scroll_range_changed(self, _min, _max):
        self.scroll.setRange(_min, _max)
        self.scroll.setPageStep(self.verticalScrollBar().pageStep())
        self.scroll.setSingleStep(self.verticalScrollBar().singleStep())
        self.scroll.setSizeIncrement(self.verticalScrollBar().sizeIncrement())

    def showEvent(self, *args, **kwargs):
        ret = super().showEvent(*args, **kwargs)
        self.animate_scroll_show(show=False, time=100)
        return ret

    def resizeEvent(self, e):
        ret = super().resizeEvent(e)
        self.scroll.move(self.width() - 11, 0)
        self.scroll.resize(11, self.height())
        model = self.model()
        if model:
            model.update_items()
        return ret

    def enterEvent(self, e):
        #print('enterEvent')
        self._entered = True
        self.animate_scroll_show(show=True)
        return super().enterEvent(e)

    def leaveEvent(self, e):
        #print('leaveEvent')
        self._entered = False
        self.animate_scroll_show(show=False)
        self.update_items_indexes(self.last_index_at)
        return super().leaveEvent(e)

    def mouseMoveEvent(self, e):

        delegate = self.itemDelegate()
        pos = (e.pos().x(), e.pos().y())

        index_at = self.indexAt(QPoint(*pos))
        if index_at.data():
            self.last_index_at = index_at

        delegate.on_mouse_pos_changed(pos)

        return super().mouseMoveEvent(e)

    def update_items_indexes(self, *lst):
        lst = [QPersistentModelIndex(ind) for ind in lst if ind]
        if len(lst) == 0:
            self.model().layoutAboutToBeChanged.emit()
            self.model().layoutChanged.emit()
        else:
            self.model().layoutAboutToBeChanged.emit(lst)
            self.model().layoutChanged.emit(lst)


class ChatsListView(ListView):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setSelectionMode(QAbstractItemView.NoSelection)

    def selectionChanged(self, selectedSelection, deselectedSelection):
        # last = self.selection_to_list(deselectedSelection)
        # lst = self.selection_to_list(selectedSelection)
        # self._selected_callback(lst)
        pass

    def selection_to_list(self, selectedSelection):
        return [ind.data() for ind in selectedSelection.indexes()]

    def clear_selection(self):
        self.clearSelection()

    def mousePressEvent(self, e):
        _cur_selected = self.indexAt(e.pos()).data()
        _current_selection = self.selectedIndexes()

        if e.button() == Qt.RightButton:
            e.ignore()
            self.open_menu_for_selected_item(e.globalPos())
        else:
            if _cur_selected:
                self._selected_callback([_cur_selected])
            return super().mousePressEvent(e)

    def open_menu_for_selected_item(self, global_pos):
        ind = self.indexAt(self.mapFromGlobal(global_pos))
        item = ind.data()
        print('[ open_menu_for_selected_item ] {}'.format(item))
        menu = self.model().make_menu(item)
        if menu:
            menu.exec_(global_pos)


class MessagesListView(ListView):

    _scroll_before_load_state = None
    _need_scroll_to_bottom_on_messages = False
    _opened = 2

    def __init__(self, parent=None):
        super().__init__(parent)

        self._after_scroll_range_change_actions = []
        self._current_selection = []

        self.setSelectionMode(QAbstractItemView.NoSelection)

        self._custom_selection = CustomSelection()
        self._scroll_last_value = 0

        self.info_label_bottom = InfoLabel(self, auto_pos=InfoLabel.BOTTOM)
        self.info_label_bottom.set_on_mouse_click_callback(self.on_info_label_click)
        self.info_label_bottom.hide()

    def set_opened(self, val):
        self._opened = val

    def on_scroll_range_changed(self, _min, _max):
        need_scroll = self.need_scroll_to_bottom_on_messages
        last_max = self.scroll.maximum()
        if self.model()._need_print_reset():
            print('!!! on_scroll_range_changed', self.scroll.value(), last_max, '->', _max,
                  "openChat:", self.is_chat_opening())
        super().on_scroll_range_changed(_min, _max)

        if need_scroll:
            self.scroll_to_bottom()
        elif self.is_loading_20():
            # self._after_scroll_range_change_actions, actions = [], self._after_scroll_range_change_actions
            # for action in actions:
            #     func = getattr(self, action) if type(action) == str else action
            #     func()
            self._scroll_to_state()
        else:
            if _max > last_max:
                last_message = self.model().last_message
                if last_message and not last_message.getDelivered() and not self.delegate.is_message_from_current_user(last_message):
                    self.show_info(self.model().new_message_text(), self.delegate.COLOR_MESSAGE_NOT_READED)

        self.set_opened(0)

    def on_info_label_click(self):
        self.scroll_to_bottom()

    def is_chat_opening(self):
        return self.model().isOpeningChat() or self._opened == 1

    def is_loading_20(self):
        return self._opened == 2

    def show_info(self, text, color=None):
        self.info_label_bottom.setText(text)
        self.info_label_bottom.set_background(color)
        self.info_label_bottom.set_color("#e7933e")
        self.info_label_bottom.show()

    def scroll_to_bottom(self):
        print('[ scroll_to_bottom ]')  # FIXME
        # if self._scroll_to_bottom not in self._after_scroll_range_change_actions:
        #     self._after_scroll_range_change_actions.append(self._scroll_to_bottom)
        #
        # self.model().reset_model(action=self._scroll_to_bottom)
        self._scroll_to_bottom()

        # if self._scroll_to_bottom not in self._after_scroll_range_change_actions:
        #     self._after_scroll_range_change_actions.append(self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        maximum = self.verticalScrollBar().maximum()
        print('_scroll_to_bottom', maximum, self.scroll.maximum())
        self.scroll.setValue(self.scroll.maximum())

    def scroll_to_state(self, maximum):
        print('[ scroll_to_state ]')
        self._scroll_before_load_state = maximum
        # if self._scroll_to_state not in self._after_scroll_range_change_actions:
        #     self._after_scroll_range_change_actions.append(self._scroll_to_state)

    def _scroll_to_state(self):
        maximum = self._scroll_before_load_state
        if maximum == None:
            return
        self._scroll_before_load_state = None
        scroll_maximum = self.scroll.maximum()
        new_value = scroll_maximum - maximum
        if self.scroll.maximum() > maximum:
            self.scroll.setValue(new_value)

    def selectionChanged(self, selectedSelection, deselectedSelection):
        lst = selectedSelection.indexes()
        if len(lst) > 0 and len(self.model()._keys_list) == 0:
            lst = []
        _new_selection = [ind.data() for ind in lst]
        if self._current_selection == _new_selection:
            return

    def change_selection(self, _new_selection):
        self._current_selection = _new_selection
        if self._selected_callback:
            self._selected_callback(_new_selection)
        self.model().update_items()

    def move_custom_selection_for_scroll(self, value):
        last_scroll = self._scroll_last_value
        d = value - last_scroll

        custom_selection: CustomSelection = self._custom_selection
        sel_start = custom_selection.start
        sel_end = custom_selection.end

        if sel_start:
            custom_selection.start = (sel_start[0], sel_start[1] - d)
        if sel_end:
            custom_selection.end = (sel_end[0], sel_end[1] - d)

        self._scroll_last_value = value

    def on_scroll_changed_real(self, value):
        self.move_custom_selection_for_scroll(value)
        scroll: QScrollBar = self.verticalScrollBar()
        on_end = scroll.maximum() == value
        self.need_scroll_to_bottom_on_messages = on_end
        if on_end:
            self.info_label_bottom.hide()

    def mousePressEvent(self, e):
        delegate = self.itemDelegate()

        if e.button() == Qt.LeftButton:

            mody = self.e_mody(e)
            if mody != Qt.ControlModifier:
                self._current_selection = []

                self._custom_selection.active = True
                self._custom_selection.start = (e.pos().x(), e.pos().y())
                self._custom_selection.end = None

                delegate.on_custom_selection_changed(self._custom_selection)

            self.update_items_indexes(self.indexAt(e.pos()))

        return super().mousePressEvent(e)

    @property
    def delegate(self):
        return self.itemDelegate()

    def e_mody(self, e):
        try:
            return int(e.modifiers())
        except:
            return 0

    def mouseMoveEvent(self, e):

        delegate = self.itemDelegate()
        pos = (e.pos().x(), e.pos().y())

        will_model_reseted = False
        if self._custom_selection.active:
            self._custom_selection.end = pos

            will_model_reseted = delegate.on_custom_selection_changed(self._custom_selection)

            self.update_items_indexes(self.indexAt(QPoint(*pos)))

        delegate.on_mouse_pos_changed(pos, will_model_reseted=will_model_reseted)

        return super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):

        # was_custom_active = self._custom_selection.active
        self._custom_selection.active = False
        delegate = self.itemDelegate()

        _cur_selected = self.indexAt(e.pos()).data()
        _current_selection = self._current_selection

        if e.button() == Qt.RightButton:

            if _cur_selected and type(_cur_selected) != LoadMessagesButton:

                if _cur_selected not in _current_selection and len(_current_selection) == 1:
                    _current_selection.clear()
                    _current_selection.append(_cur_selected)

            self.open_menu_for_selected_item(e.globalPos())

        elif e.button() == Qt.LeftButton:
            mody = self.e_mody(e)

            if _cur_selected:
                if _cur_selected in _current_selection:
                    if mody == Qt.ControlModifier:
                        _current_selection.remove(_cur_selected)
                else:
                    _current_selection.append(_cur_selected)

            if mody == Qt.ControlModifier and self._custom_selection.end != None:
                self._custom_selection.end = None
                delegate.on_custom_selection_changed(self._custom_selection)

            self.change_selection(_current_selection)

            self.update_items_indexes(self.indexAt(e.pos()))

        delegate.on_mouse_release(e)

        return super().mouseReleaseEvent(e)

    def enterEvent(self, e):

        delegate = self.itemDelegate()
        pos = (e.pos().x(), e.pos().y())

        delegate.on_mouse_pos_changed(pos)

        return super().enterEvent(e)

    def leaveEvent(self, e):

        delegate = self.itemDelegate()
        delegate.on_mouse_pos_changed((-1, -1))

        return super().leaveEvent(e)

    def clear_selection(self):
        self._current_selection = []
        self.clearSelection()

    def open_menu_for_selected_item(self, global_pos):
        item = self._current_selection[0] if self._current_selection else None
        if not item:
            ind = self.indexAt(self.mapFromGlobal(global_pos))
            item = ind.data()
        print('[ open_menu_for_selected_item ] {}'.format(item))
        menu = self.model().make_menu(item)
        if menu:
            menu.exec_(global_pos)

    @property
    def need_scroll_to_bottom_on_messages(self):
        if self.is_chat_opening():
            return True
        return self._need_scroll_to_bottom_on_messages

    @need_scroll_to_bottom_on_messages.setter
    def need_scroll_to_bottom_on_messages(self, val):
        self._need_scroll_to_bottom_on_messages = val
        # print('!!! need_scroll_to_bottom_on_messages -> {}'.format(val))


class ListDelegate(QItemDelegate):

    COLOR_ITEM_CLEAN = "#ffffff"

    round_mask = None
    _mouse_pos = (-1, -1)
    _mouse_on_item = None
    _mouse_on_image = None
    _mouse_on_name = None
    _mouse_on_link = None

    _PARTS = PChatLayout(
        PChatImage(margin_left=8, margin_top=8, margin_right=8),
        PVLayout(
            PStretch(),
            PHLayout(PLogin(debug=P_DEBUG), PChatMuted(debug=P_DEBUG), PChatPinned(debug=P_DEBUG), PLastTime(debug=P_DEBUG)),
            PLastMessage(margin_top=5, debug=P_DEBUG),
            PStretch(),
            PChatDownLine(debug=P_DEBUG),
            margin_right=10
        ), debug=P_DEBUG
    )

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

    @print_timeit
    def paint(self, painter, option, index):

        left, top, right, bottom = self.prepare_base_left_top_right_bottom(option)

        painter.setRenderHint(QPainter.Antialiasing)

        item = self.list_model.data(index)

        #print(":::", id(item))

        if type(item.item) == LoadMessagesButton:
            item.item.draw(painter, (left+50, top+20, right, bottom))
            if not self.listView.is_chat_opening() and not self.listView.is_loading_20():
                self.start_load_last_20()
            return

        if NEED_DRAW_PPARTS and self._PARTS is not None:
            bottom += 1
            if P_DEBUG:
                print("!!! top:{} bottom:{} h:{}".format(top, bottom, bottom-top))
                painter.setPen(QColor(220, 20, 20))
                painter.drawLine(left, bottom - 1, left + 50, bottom - 1)

            self._PARTS.draw(painter, self, item, (left, top, right, bottom))

        else:
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

            time_string_left = self.draw_right_text(painter, item, (left, top, right, bottom))

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

    def draw_right_text(self, painter, item, left_top_right_bottom):
        left, top, right, bottom = left_top_right_bottom

        time_string_left = -1
        time_string = self.list_model.getItemTimeString(item)
        if time_string:
            font = self.prepareTimeFont()
            painter.setFont(font)
            brect = painter.boundingRect(QRectF(0, 0, 9999, 50), time_string)
            w = brect.width()
            time_string_left = right - w - 15 #- 6 * len(time_string) - 10 #+ self.list_model.getRightAdd()
            painter.drawText(time_string_left, self.time_top(top, bottom), time_string)
        return time_string_left

    def draw_name(self, painter, item, left, top, time_string_left):
        _name = self.list_model.getItemName(item)
        _nick = self.list_model.getItemNick(item)
        _name_left = left + self._name_left_add()

        if time_string_left >= 10:
            brect = painter.boundingRect(QRectF(_name_left, 0, 9999, 50), _name)
            if brect.right() >= time_string_left:
                max_len = int((time_string_left - _name_left) / 10)
                _name = _name[:max_len] + "..."

        painter.drawText(_name_left, self.title_top(top), _name)

        if _nick and _nick != _name:
            draw_badges(painter, _nick, left+34, top+55, font_pixel_size=10,
                        bcolor='#7777cc', plus=False, factor=0.6)

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
        return option.rect.left(), option.rect.top(), option.rect.right()-self.list_model.getRightAdd(), option.rect.bottom()

    def fillRect(self, painter, item, index_row, option):
        background_color = self.get_background_color(item)

        selected = False
        selected_items = getattr(self.listView, '_current_selection', None) or []

        if item in selected_items:
            _background_color = self.selected_color(selected_items)
            if _background_color:
                background_color = _background_color

        if item and self.list_model.selected_item == item: # FIXME not using this!
            background_color = QColor(240, 240, 240)

        # option.rect.adjusted(1, 1, -1, -1)
        painter.fillRect(option.rect.adjusted(1, 0, -1, 0), background_color)  # Qt.SolidPattern)

    def selected_color(self, selected_items):
        return QColor(235, 235, 235)

    def get_background_color(self, current_item):
        return color_from_hex(self.COLOR_ITEM_CLEAN)

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
        return 12

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
                pixmap = pixmap.scaledToWidth(38/50*iw, Qt.SmoothTransformation) # 32
            sz = pixmap.size()
            actual_size = (sz.width(), sz.height())
            self.icon_drawer.draw_pixmap(painter, pixmap, (left + 8 + self.image_left_add(), top + 8), size=(iw, iw),
                    under_mouse=self._is_under_mouse(item),
                    icon_size=(iw, iw), actual_size=actual_size, alpha=1.0)

    def _is_under_mouse(self, item):
        return self._is_mouse_on_image(item)

    def _is_mouse_on_image(self, item):
        return self._mouse_on_image == item

    def _is_mouse_on_name(self, item):
        return self._mouse_on_name == item

    def is_on_item(self, item):
        if not self.listView._entered:
            return False
        ind = self.listView.indexAt(QPoint(*self._mouse_pos))
        return ind.data() == item

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
        return False

    def on_mouse_pos_changed(self, pos, will_model_reseted=False):
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

            drawer = getattr(item, 'drawer', None)
            if drawer:
                to_on_link = None
                for link in drawer.links:
                    link_rect = link.rect
                    y = pos[1]
                    if getattr(link, 'rect_local', None):  # FIXME
                        y = pos[1] - rect.top()
                    if link_rect[1] <= y <= link_rect[3] and link_rect[0] <= pos[0] <= link_rect[2]:
                        to_on_link = link
                if self._mouse_on_link != to_on_link:
                    self._mouse_on_link = to_on_link
                    changed = True

        else:
            for name in ('item', 'image', 'name'):
                if self.change_value('_mouse_on_'+name, None):
                    changed = True

        if changed:
            self.update_cursor()
            # if not will_model_reseted:
            #     #self.list_model.reset_model()
            #     self.list_model.update_items()

            lst_to_update = []
            if index:
                lst_to_update.append(index)
            if self.listView.last_index_at and self.listView.last_index_at != index:
                lst_to_update.append(self.listView.last_index_at)
            if len(lst_to_update) > 0:
                self.listView.update_items_indexes(*lst_to_update)

    def on_mouse_release(self, e):
        pass

    def update_cursor(self):
        to_shape = Qt.ArrowCursor
        if self._mouse_on_image or self._mouse_on_name or self._mouse_on_link:
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
        if (check_rect.top() <= pos[1] <= check_rect.bottom() and check_rect.left() <= pos[0] <= check_rect.right()
                and (self.need_draw_image_and_title(item) or name == '_mouse_on_item')):
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
        self.listView = listView

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
        _row = index.row()
        if _row < 0 or _row >= len(self._keys_list):
            return None
        key = self._keys_list[_row]
        item_pre = self.items_dict[key]
        item = item_from_object(item_pre, self.model_item)
        return item

    def get_current_user_id(self):
        return None

    def getCurrentItemIndex(self):
        return -1

    def getSelectedItemIndex(self):
        return -1

    def getItemName(self, item):
        return item.getName()

    def getItemNick(self, item):
        return item.getNick()

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

    def update_items(self):
        pass # FIXME !!!

    def reset_model(self, action='_reset_model_do_action', change_need_to_bottom=True):
        if self._need_print_reset():
            print('reset_model')
        if change_need_to_bottom:
            self.listView.need_scroll_to_bottom_on_messages = True

        if action not in self._reset_actions:
            self._reset_actions.append(action)

        if self._need_reset_timer:
            return
        self._need_reset_timer = Timer(0.1, self._reset_model)
        self._need_reset_timer.start()

    def _need_print_reset(self):
        return False

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
        # self.beginResetModel()
        # self.endResetModel()
        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()

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

    COLOR_MY_MESSAGE = "#eeeeee"
    COLOR_MESSAGE_NOT_READED = "#fae0c6"

    # def prepareMessageStartPosition(self, left, top):
    #     message_left = left + 50 + 16
    #     message_top = top + 38
    #     return message_left, message_top
    last_load_min_message_id = None

    _PARTS = PMessageLayout(
        PMessageImage(margin_left=8, margin_top=8, margin_right=8, margin_bottom=8, debug=P_DEBUG),
        PVLayout(
            PMessageLogin(),
            PMessage(margin_top=5, debug=P_DEBUG),
            #PStretch(debug=DEBUG),
            #PChatDownLine(),
            PHLayout(PStretch(height=2), PLastTime(), PMessageDelivered(margin_left=2)),
            margin_right=0, margin_top=5
        ), debug=P_DEBUG
    )

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
        # lst = [k for k in self.list_model._keys_list if k >= 0]
        # return min(lst) if len(lst) > 0 else None
        return self.list_model.min_message_id

    def prepareMessageText(self, item, second_text, left_top_right_bottom):
        left, top, right, bottom = left_top_right_bottom
        right -= 10

        drawer = getattr(item, 'drawer', None)
        if not drawer:
            drawer = MessageDrawer(item, self.prepareMessageFont(), second_text, self)
        drawer.rect = left_top_right_bottom

        if isinstance(item.message, LoadMessagesButton):
            return 30, item.message

        line_height = drawer.line_height
        space_width = drawer.w_width

        top_now = top
        left_now = left - space_width

        lines = drawer.lines

        new_lines_without_files = []
        new_lines = []
        message_height = 0
        quote = item.message.quote
        _add = 0
        quote_lines = []

        if quote:
            _quote_author = QuoteAuthor(quote, drawer)
            if _quote_author.line_height > 0:
                top_now += 0.8 * line_height

            _quote_author = [_quote_author]

            _quote_lines = []
            for i, line in enumerate(drawer.quote_lines):
                to_new_qoute_lines, top_now = drawer.prepare_line(line, (left, top_now, right), space_width, line_height,
                                                                lambda a: QuoteLine(a, quote, drawer))
                _quote_lines += to_new_qoute_lines

            if [['']] == _quote_lines:
                _quote_lines.clear()

            _quote_file = []
            if drawer.quote_file:
                _add += drawer.quote_file.line_height
                _quote_file.append(drawer.quote_file)

            if len(_quote_lines) > 0:
                _quote_lines[-1].is_last_quote_line = True

            new_lines += _quote_author + _quote_file + _quote_lines
            new_lines_without_files += _quote_author + _quote_lines

            _add += 0.8 * line_height
            top_now += 0.8 * line_height

        for line in lines:
            # top_now += line_height
            to_new_lines, top_now = drawer.prepare_line(line, (left, top_now, right), space_width, line_height)

            new_lines += to_new_lines
            new_lines_without_files += to_new_lines

        message_height = (len(new_lines_without_files)) * line_height + 0.5*line_height + _add

        if drawer.file_line:
            file_line = drawer.file_line
            message_height += file_line.line_height

            new_lines.insert(0, file_line)
            if second_text == drawer.file_line.filename: # FIXME
                new_lines = new_lines[:1]

        return message_height, new_lines

    def drawMessageText(self, painter, line_height_and_lines, left_top_right_bottom, item):
        left, top, right, bottom = left_top_right_bottom
        right -= 10
        line_height, lines = line_height_and_lines

        mouse_pos = self._mouse_pos

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
                self.start_load_last_20()

        else:
            selected_text = None
            selected_lines = []
            last_selected_line_i = -1

            for i, words_line in enumerate(lines):

                line_height = words_line.line_height
                bottom_now = top_now + line_height

                selected_line = words_line.draw_line(drawer, painter, (left, top_now, right, bottom_now), sel_start, sel_end)
                if selected_line != None:
                    if last_selected_line_i >= 0:
                        ln = i - last_selected_line_i - 1
                        if ln > 0:
                            selected_lines += [''] * ln

                    selected_lines.append(selected_line)
                    last_selected_line_i = i

                top_now = bottom_now

            _current_selection = self.listView._current_selection
            if len(selected_lines) > 0:
                selected_text = '\n'.join(selected_lines)
                if drawer.message not in _current_selection:
                    _current_selection.append(drawer.message)

            else:
                custom_selection: CustomSelection = self.listView._custom_selection
                if custom_selection.active and drawer.message in _current_selection:
                    _current_selection.remove(drawer.message)

            drawer.message.message.set_selected_text(selected_text)

    def start_load_last_20(self):
        min_message_id = self.get_min_message_id()
        if self.last_load_min_message_id != min_message_id:
            self.listView.set_opened(2)
            val, maximum = self.listView.verticalScrollBar().value(), self.listView.verticalScrollBar().maximum()
            # self.listView.scroll.setValue(50)
            self.listView.scroll_to_state(maximum)
            self.last_load_min_message_id = min_message_id
            self.list_model.on_need_download_20(min_message_id)

    def on_mouse_release(self, e):
        ind = self.listView.indexAt(e.pos())
        message = ind.data()

        if not message:
            return
        ind_rect = self.listView.visualRect(ind)

        # FIXME simplify...
        if e.button() == Qt.LeftButton:

            if type(message.item) == LoadMessagesButton:
                #self.last_load_min_message_id = -1
                self.start_load_last_20()

            else:

                drawer: MessageDrawer = message.drawer

                print('LINKS({}): {} : {}'.format(id(drawer), drawer.links, e.pos().x()))

                if drawer.links:

                    pos = (e.pos().x(), e.pos().y())#-ind_rect.top())

                    link = None
                    rect = None
                    for w_drawer in drawer.links:
                        rect = w_drawer.rect
                        y = pos[1]
                        if getattr(w_drawer, 'rect_local', None): # FIXME
                            y -= ind_rect.top()
                        if rect[0] <= pos[0] <= rect[2] and rect[1] <= y <= rect[3]:
                            link = w_drawer

                    print('\t-> ON LINK: {} : {} : {}'.format(link, pos, rect))
                    if link:

                        if hasattr(link, 'word_type') and link.word_type == WORD_TYPE_LINK:
                            if link.url.startswith('#INPUT_CALL:'):
                                self.list_model.on_chat_event('INPUT_CALL', link.url[len('#INPUT_CALL:'):])
                            else:
                                import webbrowser
                                webbrowser.open(link.url, new=0, autoraise=True)

                        elif hasattr(link, 'line_type') and link.line_type == LINE_TYPE_FILE:
                            file_uuid = link.file_uuid
                            filename = link.filename
                            filesize = link.filesize
                            if file_uuid and len(file_uuid) > 1:
                                file_path = getDownloadsFilePath(filename, file_uuid)
                                if exists(file_path):
                                    self.list_model.on_need_open_file(file_path, filesize, file_uuid)
                                else:
                                    self.list_model.on_need_download_file(file_uuid, filename)

    def get_background_color(self, current_item):

        message = current_item.message
        background_color = self.COLOR_ITEM_CLEAN

        if type(message) != LoadMessagesButton:

            if self.is_message_from_current_user(message):
                background_color = self.COLOR_MY_MESSAGE

            elif not message.getDelivered():
                background_color = self.COLOR_MESSAGE_NOT_READED
                self.list_model.add_to_delivered_by_gui(message.mes_id)

        return color_from_hex(background_color)

    def is_message_from_current_user(self, message):
        current_user_id = self.list_model.get_current_user_id()
        return current_user_id == message.sender_id

    def get_delivered_icon(self, message):
        delivered_icon = None
        current_user_id = self.list_model.get_current_user_id()

        if current_user_id == message.sender_id:
            delivered_icon = "check"

            if message.getDelivered():
                delivered_icon = "check_all"

        return delivered_icon

    def need_draw_image_and_title(self, item):
        item = item.item
        if type(item) == LoadMessagesButton:
            return False
        if item.last_item and item.sender == item.last_item.sender:
            return False
        return True

    def draw_right_text(self, painter, message, left_top_right_bottom):
        left, top, right, bottom = left_top_right_bottom

        # right bottom text with date and delivered
        # painter.setPen(QColor(self.INFO_COLOR))
        # font = self.simple_font
        # font.setBold(False)
        # font.setPixelSize(12)
        font = self.prepareTimeFont()
        painter.setFont(font)
        #font = painter.font()
        font_h = QFontMetrics(font).height()

        message = message.message

        delivered_icon = self.get_delivered_icon(message)

        padding_x = 5
        padding_y = 5

        # render icon delivered
        if delivered_icon:
            # icon_pixmap = delivered_icon.pixmap(QSize(QFontMetrics(font).height(), QFontMetrics(font).height()))
            # painter.drawImage(QPointF(right - (QFontMetrics(font).height() + padding_x), #+ self.listView.width_add,
            #                           bottom - font_h - padding_y), icon_pixmap.toImage())  # FIXME 5...
            deliv_sz = (16, 16)
            draw_icon_from_file(painter, delivered_icon,
                                right - (deliv_sz[0] + padding_x), bottom - deliv_sz[1] - padding_y,
                                w=deliv_sz[0], h=deliv_sz[1])

        date_text = "{}".format(message.getTimeString())
        date_text_width = QFontMetrics(font).width(date_text)

        _top_left = QPoint(
            right - (date_text_width + padding_x + 5 + QFontMetrics(font).height()), #+ self.listView.width_add,
            bottom - font_h - padding_y)

        dateTextRect = QRect(_top_left, QSize(date_text_width, QFontMetrics(font).height()))

        painter.drawText(dateTextRect, Qt.AlignLeft, date_text)

        # painter.drawLine(left, bottom - font_h - self.padding_y, right, bottom - font_h - self.padding_y)
        # painter.drawLine(left, bottom, right, bottom)

        return right

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
        self.list_model.update_items()
        return True

    def _is_under_mouse(self, item):
        return self._is_mouse_on_image(item) or self._is_mouse_on_name(item)

    def prepare_pen_and_font_for_name(self, painter: QPainter, item):
        pen, font = super().prepare_pen_and_font_for_name(painter, item)
        if self._is_mouse_on_name(item) or self._is_mouse_on_image(item):
            font.setUnderline(True)
        return pen, font

    def selected_color(self, selected_items):
        if len(selected_items) == 1:
            return
        return color_from_hex('#fae298')


class MessagesListModel(ListModel):

    is_only_files = False
    is_only_favorites = False
    min_message_id = -1

    def __init__(self, listView):
        super().__init__(listView, list_delegate_cls=MessagesListDelegate)

    def on_need_download_20(self, min_message_id):
        pass

    def isOpeningChat(self):
        return False

    def _need_print_reset(self):
        return True

    def getItemHeight(self, item, option):

        #message_left, message_top = self.delegate.prepareMessageStartPosition(0, 0)

        #left_top_right_bottom = message_left, message_top, right, 99999
        if type(item.message) != LoadMessagesButton:

            second_text = self.getItemSecondText(item)
            if second_text:
                right = option.rect.right()

                m_rect, max_bottom = self.delegate._PARTS.message_part.calc_rect(item, self.delegate, right)

                message_height, new_lines = self.delegate.prepareMessageText(item, second_text, m_rect)
                #h = (len(new_lines)) * line_height
                # h_top = message_top - option.rect.top()
                # h = message_height + h_top + 20
                h = message_height + max_bottom
                return h

        return 70

    def new_message_text(self):
        return "New message"

    def set_items_dict(self, val):
        keys = list(val.keys())
        min_message_id = min(keys) if len(keys) > 0 else None
        self.min_message_id = min_message_id

        messages_dict = { int(k):v for k, v in val.items() if self.filt(k, v) }
        keys_list = sorted(list(messages_dict.keys()), key=lambda key: (messages_dict[key].datetime, key))

        if len(messages_dict) >= 20 or (self.is_only_files or self.is_only_favorites) or min_message_id == None: # FIXME
            messages_dict.keys()
            messages_dict[-1] = LoadMessagesButton()
            keys_list.insert(0, -1)

            # if self.is_only_files and len(keys_list) == 1:
            #     self.delegate.last_load_min_message_id = -1

        return messages_dict, keys_list

    @property
    def last_message(self):
        if not self._keys_list:
            return None
        key = self._keys_list[-1]
        m = self._items_dict.get(key, None)
        if hasattr(m, 'NOT_MESSAGE'):
            m = None
        return m

    def filt(self, k, m):
        ok = True

        if self.is_only_files and not m.has_file:
            ok = False

        if self.is_only_favorites and not self.is_message_in_favorites(m):
            ok = False

        return ok


    def make_menu(self, message_item):
        pass

    def add_to_delivered_by_gui(self, mes_id):
        pass

    def on_need_download_file(self, file_uuid, filename):
        pass

    def on_need_open_file(self, file_path, filesize, file_uuid):
        pass

    def on_chat_event(self, event, *args, **kwargs):
        pass

    def getRightAdd(self):
        return 10

    def is_message_in_favorites(self, mes):
        return False


class ListModelItem:

    def getName(self):
        raise NotImplementedError

    def getNick(self):
        return None

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

    NOT_MESSAGE = True

    def __init__(self, text=None):
        if text is not None:
            self.text = text

    def draw(self, painter, left_top_right_bottom):
        left, top, right, bottom = left_top_right_bottom
        left, top, right, bottom = left-28, top-14, right-20, bottom-14

        painter.drawText(QRect(QPoint(left, top), QPoint(right, bottom)), Qt.AlignCenter, self.text)
        painter.drawRect(left+11, top+4, right-left-22, bottom-top-8)

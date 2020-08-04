

def item_from_object(obj, item_cls):
    if not obj:
        return None
    item = getattr(obj, 'item', None)
    if not item:
        item = item_cls(obj)
        obj.item = item
    return item

# rgba(140,95,56,255); ;
V_SCROLL_SHOW = """
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 11px;
    margin: 0px 1px 0px 0px;
}
QScrollBar::handle:vertical {
    background: rgba(140,140,140,255);
    margin: 2px 2px 2px 2px;
    min-height: 20px;
    border-radius: 3px;
}
QScrollBar::add-line:vertical {
    background: rgba(0,0,0,0);
    height: 0px;
    subcontrol-position: bottom;
    subcontrol-origin: margin;
}
QScrollBar::sub-line:vertical {
    background: rgba(0,0,0,0);
    height: 0px;
    subcontrol-position: top;
    subcontrol-origin: margin;
}
MessagesListView {
    background: rgba(229,221,213,255);
}
"""

MAIN_STYLESHEET = """
QListView {border-right: 1px solid #cccccc; background-color: #ffffff;}
QPushButton {background-color: #ffffff; border: 1px solid #cccccc; border-radius: 5px; padding: 5px; padding-left: 10px; padding-right: 10px; min-width: 80px; }
QPushButton:hover {background-color: #eeeeee;}
QPushButton#updateButton { background-color: #ffc107; border: 1px solid #d19f0a; border-radius: none; }
QPushButton#updateButton:hover {background-color: #f9d158;}
QDialog { background: #ffffff; font-size: 14px; font-family: Arial; }
QDialog QLabel { color: #333333; font-size: 14px; font-family: Arial; }
QDialog QPushButton { color: #333333; font-size: 14px; font-family: Arial; }
"""

FULL_STYLESHEET = V_SCROLL_SHOW + MAIN_STYLESHEET
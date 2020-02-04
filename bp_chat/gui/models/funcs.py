

def item_from_object(obj, item_cls):
    if not obj:
        return None
    item = getattr(obj, 'item', None)
    if not item:
        item = item_cls(obj)
        obj.item = item
    return item

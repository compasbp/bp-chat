

def item_from_object(obj, item_cls):
    item = getattr(obj, 'item', None)
    if not item:
        item = item_cls(obj)
        obj.item = item
    return item

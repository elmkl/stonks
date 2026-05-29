def find(items, key, value):
    for item in items:
        if item.get(key, "").upper() == value.upper():
            return item
    return None
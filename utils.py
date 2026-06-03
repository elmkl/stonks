def find(items, key, value):
    for item in items:
        if item.get(key, "").upper() == value.upper():
            return item
    return None

def _float(v, default=0.0):
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        v = v.strip()
        if v in ("-", ""):
            return default
        try:
            return float(v)
        except ValueError:
            return default
    return default
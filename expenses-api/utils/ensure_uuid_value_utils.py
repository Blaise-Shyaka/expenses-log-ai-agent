from uuid import UUID

def ensure_uuid_value(value:UUID|str|bytes)->UUID:
    if isinstance(value,UUID):
        return value
    elif isinstance(value,bytes):
        return UUID(bytes=value)
    else:
        return UUID(str(value))

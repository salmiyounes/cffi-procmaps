def to_bytes(s: str | bytes) -> bytes:
    if isinstance(s, bytes):
        return s
    return str(s).encode()


def to_str(s: str | bytes) -> str:
    if isinstance(s, str):
        return s
    return bytes(s).decode()

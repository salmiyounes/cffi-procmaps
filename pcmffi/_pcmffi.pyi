from typing import Any
from cffi import FFI

class lib:
    @staticmethod
    def pmparser_parse(pid: int, it: Any) -> int:
        ... 

    @staticmethod
    def pmparser_free(it: Any) -> None:
        ...

ffi: FFI
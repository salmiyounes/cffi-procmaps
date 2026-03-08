from typing import Any
from cffi import FFI

class lib:
    @staticmethod
    def pmparser_parse(pid: int, it: Any) -> int:
        ... 

    @staticmethod
    def pmparser_free(it: Any) -> None:
        ...
    
    @staticmethod
    def pmparser_parse_line(buf: bytes, mem_reg: Any) -> None:
        ...

ffi: FFI
from typing import TypeAlias, Any
from cffi import FFI

CData: TypeAlias = Any

class lib:
    @staticmethod
    def pmparser_parse(pid: int, it: CData) -> int: ... 

    @staticmethod
    def pmparser_free(it: CData) -> None: ...
    
    @staticmethod
    def pmparser_parse_line(buf: bytes, mem_reg: CData) -> None: ...
    
    @staticmethod
    def pmparser_next(it: CData) -> CData: ...
    

ffi: FFI
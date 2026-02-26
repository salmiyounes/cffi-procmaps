from typing import TypeAlias, Optional, Iterator, List
from dataclasses import dataclass
from .exceptions import (
    ProcMapsOpenFileError,
    ProcMapsReadFileError,
    ProcMapsMemoryError,
)
from ._pcmffi import ffi, lib

PROCMAPS_ERROR_T: TypeAlias = int

PROCMAPS_SUCCESS: PROCMAPS_ERROR_T = 0
PROCMAPS_ERROR_OPEN_MAPS_FILE: PROCMAPS_ERROR_T = 1
PROCMAPS_ERROR_READ_MAPS_FILE: PROCMAPS_ERROR_T = 2
PROCMAPS_ERROR_MALLOC_FAIL: PROCMAPS_ERROR_T = 3

PROCMAPS_MAP_TYPE: TypeAlias = int

PROCMAPS_MAP_FILE: PROCMAPS_MAP_TYPE = 0
PROCMAPS_MAP_STACK: PROCMAPS_MAP_TYPE = 1
PROCMAPS_MAP_STACK_TID: PROCMAPS_MAP_TYPE = 2
PROCMAPS_MAP_VDSO: PROCMAPS_MAP_TYPE = 3
PROCMAPS_MAP_VVAR: PROCMAPS_MAP_TYPE = 4
PROCMAPS_MAP_VSYSCALL: PROCMAPS_MAP_TYPE = 5
PROCMAPS_MAP_HEAP: PROCMAPS_MAP_TYPE = 6
PROCMAPS_MAP_ANON_PRIV: PROCMAPS_MAP_TYPE = 7
PROCMAPS_MAP_ANON_SHMEM: PROCMAPS_MAP_TYPE = 8
PROCMAPS_MAP_ANON_MMAPS: PROCMAPS_MAP_TYPE = 9
PROCMAPS_MAP_OTHER: PROCMAPS_MAP_TYPE = 10

proc_map_types: List[str] = [
    "file",
    "process_stack",
    "thread_stack",
    "VDSO",
    "heap",
    "anon_private",
    "anon_shared",
    "anonymous",
    "vvar",
    "vsyscall",
    "other",
]


def error(err: PROCMAPS_ERROR_T):
    msg: str = {
        1: "Failed to open the maps file (check /proc)",
        2: "Failed to read from the maps file",
        3: "Internal memory allocation (malloc) failed",
    }[err]

    if err == PROCMAPS_ERROR_OPEN_MAPS_FILE:
        raise ProcMapsOpenFileError(msg)
    elif err == PROCMAPS_ERROR_READ_MAPS_FILE:
        raise ProcMapsReadFileError(msg)
    elif err == PROCMAPS_ERROR_MALLOC_FAIL:
        raise ProcMapsMemoryError(msg)


def byte_2_str(b: bytes) -> str:
    return b.decode("utf-8")


def proc_map_iterator(procmaps_it) -> Iterator["MemoryRegion"]:  # type: ignore
    while (mem_reg := lib.pmparser_next(procmaps_it)) != ffi.NULL:  # type: ignore
        offset: int
        pathname: bytes = b""
        anon_name: bytes = b""

        _type = mem_reg.map_type
        if _type == PROCMAPS_MAP_FILE:
            offset = mem_reg.offset
            pathname = ffi.string(mem_reg.pathname)
        elif _type == PROCMAPS_MAP_ANON_PRIV or _type == PROCMAPS_MAP_ANON_SHMEM:
            anon_name = ffi.string(mem_reg.map_anon_name)
        elif _type == PROCMAPS_MAP_OTHER:
            pathname = ffi.string(mem_reg.pathname)

        yield MemoryRegion(
            start_addr=int(ffi.cast("uintptr_t", mem_reg.addr_start)),
            end_addr=int(ffi.cast("uintptr_t", mem_reg.addr_end)),
            length=mem_reg.length,
            is_r=bool(mem_reg.is_r),
            is_w=bool(mem_reg.is_w),
            is_x=bool(mem_reg.is_x),
            is_p=bool(mem_reg.is_p),
            offset=offset,
            dev_major=mem_reg.dev_major,
            dev_minor=mem_reg.dev_minor,
            inode=mem_reg.inode,
            pathname=byte_2_str(pathname),
            map_type=mem_reg.map_type,
            map_anon_name=byte_2_str(anon_name),
            file_deleted=bool(mem_reg.file_deleted),
        )


@dataclass
class MemoryRegion:
    start_addr: int  # void *addr_start
    end_addr: int  # void *addr_end
    length: int  # size_t length
    is_r: bool  # short is_r (interpreted as boolean)
    is_w: bool  # short is_w
    is_x: bool  # short is_x
    is_p: bool  # short is_p
    offset: int  # size_t offset
    dev_major: int  # unsigned int dev_major
    dev_minor: int  # unsigned int dev_minor
    inode: int  # unsigned long long inode
    pathname: Optional[str]  # char *pathname
    map_type: PROCMAPS_MAP_TYPE  # procmaps_map_type
    map_anon_name: Optional[str]  # char map_anon_name[]
    file_deleted: bool  # short file_deleted

    def __len__(self):
        return self.end_addr - self.start_addr

    def is_readable(self) -> bool:
        return self.is_r

    def is_writable(self) -> bool:
        return self.is_w

    def is_executable(self) -> bool:
        return self.is_x

    def is_private(self) -> bool:
        return self.is_p

    def is_file_deleted(self) -> bool:
        return self.file_deleted

    @property
    def type(self) -> str:
        return proc_map_types[self.map_type]


class ProcMaps:
    def __init__(self, pid: int = -1) -> None:
        self._pid: int = pid
        self._it = ffi.new("struct procmaps_iterator *")
        self._memory_regs: List["MemoryRegion"] = []
        err = self._initialize()
        if err != PROCMAPS_SUCCESS:
            error(err)

    def __len__(self):
        return len(self._memory_regs)

    def __getitem__(self, key: int) -> "MemoryRegion":
        return self._memory_regs[key]

    def __iter__(self):
        return iter(self._memory_regs)

    def __del__(self) -> None:
        lib.pmparser_free(self._pointer)

    @property
    def pid(self) -> int:
        return self._pid

    @property
    def _pointer(self):  # type: ignore
        return self._it

    @pid.setter
    def pid(self, new_pid: int) -> None:
        self._pid = new_pid

    def push(self, item: object) -> None:
        if not isinstance(item, MemoryRegion):
            raise TypeError(f"Item is not of type {MemoryRegion.__name__}")
        self._memory_regs.append(item)

    def _initialize(self) -> PROCMAPS_ERROR_T:
        err = lib.pmparser_parse(self.pid, self._pointer)
        if err == PROCMAPS_SUCCESS:
            for m in proc_map_iterator(self._pointer):
                self.push(m)
        return PROCMAPS_ERROR_T(err)

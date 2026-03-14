from typing import TypeAlias, Optional, Iterator, List, Any, Self, Dict
from dataclasses import dataclass
from .exceptions import (
    ProcMapsOpenFileError,
    ProcMapsReadFileError,
    ProcMapsMemoryError,
)
from .utils import to_bytes, to_str
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

proc_map_exception_msg: Dict[int, str] = {
    PROCMAPS_ERROR_OPEN_MAPS_FILE: "Failed to open the maps file (check /proc)",
    PROCMAPS_ERROR_READ_MAPS_FILE: "Failed to read from the maps file",
    PROCMAPS_ERROR_MALLOC_FAIL: "Internal memory allocation (malloc) failed",
}

error_mapping: Dict[int, Any] = {
    PROCMAPS_ERROR_MALLOC_FAIL: ProcMapsMemoryError,
    PROCMAPS_ERROR_OPEN_MAPS_FILE: ProcMapsOpenFileError,
    PROCMAPS_ERROR_READ_MAPS_FILE: ProcMapsReadFileError,
}


def ffi_2_string(cdata: Any) -> str:
    return to_str(ffi.string(cdata))


def ffi_cast(cdecl: str, cdata: Any):
    return ffi.cast(cdecl, cdata)


def new_procmaps_iterator_struct():  # type: ignore
    return ffi.new("struct procmaps_iterator *")


def proc_map_iterator(procmaps_it) -> Iterator["MemoryRegion"]:  # type: ignore
    next_map: Any = getattr(lib, "pmparser_next")
    while (mem_reg := next_map(procmaps_it)) != ffi.NULL:  # type: ignore
        yield MemoryRegion.from_procmaps_struct(mem_reg)


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

    def __contains__(self, item: int) -> bool:
        return item >= self.start_addr and item < self.end_addr

    def __str__(self) -> str:
        builder: List[str] = []

        # Address Range
        addr_range = "0x%.12x-0x%.12x\t" % (
            self.start_addr,
            self.end_addr,
        )
        builder.append(addr_range)

        # Permissions
        perms = (
            f"{'r' if self.is_readable() else '-'}"
            f"{'w' if self.is_writable() else '-'}"
            f"{'x' if self.is_executable() else '-'}"
            f"{'p' if self.is_private() else 's'}"
        )
        builder.append(f"{perms} ")

        # Lenght and Map Type
        builder.append(f"{self.length}\n")
        builder.append(f"{self.type}\t")

        if self.map_type == PROCMAPS_MAP_FILE:
            builder.append(f"Offset:{self.offset} {self.pathname}")

        elif self.map_type in [PROCMAPS_MAP_ANON_PRIV, PROCMAPS_MAP_ANON_SHMEM]:
            builder.append(f"{self.map_anon_name}")

        elif self.map_type == PROCMAPS_MAP_OTHER:
            builder.append(f"{self.pathname}")

        # Inode and Device Info
        builder.append(
            f"\ninode :{self.inode}\ndevice:{self.dev_major}:{self.dev_minor}\n"
        )

        return "".join(builder)

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

    @classmethod
    def from_str(cls, maps_data: str | bytes) -> Self:
        if isinstance(maps_data, str):
            maps_data = to_bytes(maps_data)
        dummy = ffi.new("struct procmaps_struct *")
        lib.pmparser_parse_line(maps_data, dummy)
        return cls.from_procmaps_struct(dummy)

    @classmethod
    def from_procmaps_struct(cls, mem_reg: Any) -> Self:
        map_type: int = mem_reg.map_type
        offset: int = mem_reg.offset if map_type == PROCMAPS_MAP_FILE else 0
        pathname: str = (
            ffi_2_string(mem_reg.pathname)
            if map_type in [PROCMAPS_MAP_FILE, PROCMAPS_MAP_OTHER]
            else ""
        )
        anon_name: str = (
            ffi_2_string(mem_reg.map_anon_name)
            if map_type in [PROCMAPS_MAP_ANON_PRIV, PROCMAPS_MAP_ANON_SHMEM]
            else ""
        )

        return cls(
            start_addr=int(ffi_cast("uintptr_t", mem_reg.addr_start)),
            end_addr=int(ffi_cast("uintptr_t", mem_reg.addr_end)),
            length=mem_reg.length,
            is_r=bool(mem_reg.is_r),
            is_w=bool(mem_reg.is_w),
            is_x=bool(mem_reg.is_x),
            is_p=bool(mem_reg.is_p),
            offset=offset,
            dev_major=mem_reg.dev_major,
            dev_minor=mem_reg.dev_minor,
            inode=mem_reg.inode,
            pathname=pathname,
            map_type=mem_reg.map_type,
            map_anon_name=anon_name,
            file_deleted=bool(mem_reg.file_deleted),
        )


class ProcMaps:
    def __init__(self, pid: int = -1) -> None:
        self._pid: int = pid
        self._it = new_procmaps_iterator_struct()
        self._initialize()

    def __del__(self) -> None:
        lib.pmparser_free(self.pointer)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        lib.pmparser_free(self.pointer)

    @property
    def maps(self) -> "ProcMapsGenerator":
        return ProcMapsGenerator(self)

    @property
    def pid(self) -> int:
        return self._pid

    @property
    def pointer(self):  # type: ignore
        return self._it

    def _initialize(self) -> None:
        err = lib.pmparser_parse(self.pid, self.pointer)
        if err == PROCMAPS_SUCCESS:
            return

        exception_cls = error_mapping.get(err)
        if exception_cls:
            raise exception_cls(proc_map_exception_msg.get(err))

    @classmethod
    def from_pid(cls, pid: int) -> Self:
        return cls(pid)


class ProcMapsGenerator:
    def __init__(self, procmaps: ProcMaps) -> None:
        self.procmaps = procmaps

    def __iter__(self) -> Iterator[MemoryRegion]:
        return proc_map_iterator(self.procmaps.pointer)

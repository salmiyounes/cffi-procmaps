
class ProcMapsOpenFileError(Exception):
    """Raised when the maps file cannot be opened."""
    pass

class ProcMapsReadFileError(Exception):
    """Raised when the maps file cannot be read."""
    pass

class ProcMapsMemoryError(MemoryError):
    """Raised when an allocation fails (inherits from built-in MemoryError)."""
    pass
import logging
import os
import sys
import unittest
from textwrap import dedent
from pcmffi import MemoryRegion, ProcMaps


class RaiseLogHandler(logging.StreamHandler):
    def handle(self, record):
        super().handle(record)
        raise RuntimeError("was expecting no log messages")


class TestProcMaps(unittest.TestCase):
    def check_map_properties(self, map_: MemoryRegion):
        self.assertIsInstance(map_.start_addr, int)
        self.assertIsInstance(map_.end_addr, int)

        # Test contains
        self.assertTrue(map_.start_addr in map_)
        self.assertFalse(map_.end_addr in map_)

        self.assertIsInstance(map_.is_r, bool)
        self.assertIsInstance(map_.is_w, bool)
        self.assertIsInstance(map_.is_x, bool)
        self.assertIsInstance(map_.is_p, bool)
        self.assertIsInstance(map_.offset, int)
        self.assertIsInstance(map_.dev_major, int)
        self.assertIsInstance(map_.dev_minor, int)
        self.assertIsInstance(map_.inode, int)

        self.assertTrue(isinstance(map_.pathname, str) or map_.pathname is None)

    def test_str(self):
        map_ = MemoryRegion.from_str(
            "55d5564b4000-55d5564b6000 r--p 00000000 08:11 6553896 /bin/cat"
        )

        self.assertEqual(
            str(map_),
            dedent("""\
                                           0x55d5564b4000-0x55d5564b6000\tr--p 8192
                                           file\tOffset:0 /bin/cat
                                           inode :6553896
                                           device:8:11
                                           """),
        )

    def test_from_str(self):
        maps = MemoryRegion.from_str(
            "55d5564b4000-55d5564b6000 r--p 00000000 08:11 6553896 /bin/cat"
        )
        self.check_map_properties(maps)

    def test_from_pid(self):
        with ProcMaps.from_pid(os.getpid()) as maps:
            for map_ in maps:
                self.check_map_properties(map_)


if __name__ == "__main__":
    verbosity = sum(
        arg.count("v") for arg in sys.argv if all(c == "v" for c in arg.lstrip("-"))
    )
    verbosity += sys.argv.count("--verbose")

    if verbosity >= 2:
        logging.basicConfig(level=logging.DEBUG)

    raise_log_handler = RaiseLogHandler()
    raise_log_handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(raise_log_handler)

    unittest.main()

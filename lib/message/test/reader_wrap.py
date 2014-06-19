"""
pure Python wrapper around libreader.so using ctypes
"""

import ctypes

lib = ctypes.cdll.LoadLibrary('libreader.so')
from message_wrap import Message, as_array

class MessageReader:
    def __init__(self, r=None):
        self.r = r or lib.message_reader_new()
        if not self.r:
            raise RuntimeError("could not create MessageReader object")
        self._buffers = [] # keep references so they do not get gc'd

    def __del__(self):
        try:
            lib.message_reader_delete(self.r)
        except AttributeError:
            pass # lib was already garbage collected

    def reset(self):
        lib.message_reader_reset(self.r)

    def add_buffer(self, buf):
        a = as_array(buf)
        n = len(buf)
        self._buffers.append(a)
        fail = lib.message_reader_add_buffer(self.r, a, n)
        if fail:
            raise RuntimeError("could not add buffer")

    def get_message(self):
        m = lib.message_reader_get_message(self.r)
        if not m and not self.is_empty:
            raise RuntimeError("could not read message")
        return Message(m) if m else None

    def get_depleted(self):
        return list(lib.message_reader_get_depleted(self.r))

    @property
    def is_empty(self):
        return bool(lib.message_reader_is_empty(self.r))

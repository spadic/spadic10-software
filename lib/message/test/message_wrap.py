"""
pure Python wrapper around libmessage.so using ctypes
"""

import ctypes

lib = ctypes.cdll.LoadLibrary('libmessage.so')

def as_array(words, dtype=ctypes.c_uint16):
    return (len(words) * dtype)(*words)

class Message:
    """
    Straightforward mapping of C API to Python class.
    """

    #---- create, destroy, fill ---------------------------

    def __init__(self):
        m = lib.message_new()
        if not m:
            raise RuntimeError("could not create Message object")
        self.m = m

    def __del__(self):
        try:
            lib.message_delete(self.m)
        except AttributeError:
            pass # lib was garbage collected before the last Message object

    def reset(self):
        lib.message_reset(self.m)

    def read_from_buffer(self, buf):
        return lib.message_read_from_buffer(self.m, as_array(buf), len(buf))

    #---- query status/type -------------------------------

    def is_complete(self):
        return lib.message_is_complete(self.m)

    def is_valid(self):
        return lib.message_is_valid(self.m)

    def is_hit(self):
        return lib.message_is_hit(self.m)

    def is_hit_aborted(self):
        return lib.message_is_hit_aborted(self.m)

    def is_buffer_overflow(self):
        return lib.message_is_buffer_overflow(self.m)

    def is_epoch_marker(self):
        return lib.message_is_epoch_marker(self.m)

    def is_epoch_out_of_sync(self):
        return lib.message_is_epoch_out_of_sync(self.m)

    def is_info(self):
        return lib.message_is_info(self.m)

    #---- access data -------------------------------------

    def group_id(self):
        return lib.message_get_group_id(self.m)

    def channel_id(self):
        return lib.message_get_channel_id(self.m)

    def timestamp(self):
        return lib.message_get_timestamp(self.m)

    def samples(self):
        s = lib.message_get_samples(self.m)
        if not s:
            return None
        n = lib.message_get_num_samples(self.m)
        p = ctypes.POINTER(n * ctypes.c_int16)
        return list(ctypes.cast(s, p).contents)

    def hit_type(self):
        return lib.message_get_hit_type(self.m)

    def stop_type(self):
        return lib.message_get_stop_type(self.m)

    def buffer_overflow_count(self):
        return lib.message_get_buffer_overflow_count(self.m)

    def epoch_count(self):
        return lib.message_get_epoch_count(self.m)

    def info_type(self):
        return lib.message_get_info_type(self.m)

    #---- now add some convenience ------------------------

    def as_text(self):
        return str(self.samples())

import ctypes
import struct

lib = ctypes.cdll.LoadLibrary("libmessage.so")

class Message(ctypes.Structure):
    _fields_ = [("group_id", ctypes.c_ubyte),
                ("channel_id", ctypes.c_ubyte),
                ("timestamp", ctypes.c_ushort),
                ("data", ctypes.POINTER(ctypes.c_ushort)),
                ("num_data", ctypes.c_ubyte),
                ("hit_type", ctypes.c_ubyte),
                ("stop_type", ctypes.c_ubyte),
                ("buffer_overflow_count", ctypes.c_ubyte),
                ("epoch_count", ctypes.c_ushort),
                ("info_type", ctypes.c_ubyte),
                ("valid", ctypes.c_ubyte)]

def data_from_bytes(b):
    fmt = '>%iH'%(len(b)/2)
    return struct.unpack(fmt, b)

def data_from_string(s):
    return [int(x, 16) for x in s.split()]

def read_messages(data):
    n = len(data)
    t = ctypes.c_ushort*n
    w = t(*data)
    count = lib.seek_message_start_all_wrap(w, n)
    print "result:", count


if __name__=='__main__':
    s = """
    8123
    9456
    A789
    1234
    2345
    3456
    BABC
    """
    d = data_from_string(s)
    read_messages(d)


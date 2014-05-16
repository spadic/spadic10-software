import ctypes
import struct

message = ctypes.cdll.LoadLibrary("libmessage.so")

def data_from_bytes(b):
    fmt = '>%iH'%(len(b)/2)
    return struct.unpack(fmt, b)

def data_from_string(s):
    return [int(x, 16) for x in s.split()]

def read_messages(data):
    n = len(data)
    t = ctypes.c_ushort*n
    w = t(*data)
    count = message.seek_message_start_all_wrap(w, n)
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


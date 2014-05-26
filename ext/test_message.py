#!/usr/bin/env python

import ctypes
import struct

lib = ctypes.cdll.LoadLibrary("libtest_message.so")

def data_from_bytes(b):
    fmt = '>%iH'%(len(b)/2)
    return struct.unpack(fmt, b)

def data_from_string(s):
    return [int(x, 16) for x in s.split()]

def read_messages(data):
    n = len(data)
    t = ctypes.c_uint16*n
    w = t(*data)
    count = lib.test_message_read(w, n)
    print "result:", count

if __name__=='__main__':
    import sys
    read_messages([int(x, 16) for x in sys.stdin])


import ctypes

message = ctypes.cdll.LoadLibrary("libmessage.so")
words = ctypes.c_uint16 * 8

w = words(*[1, 0x80ab, 0x9123, 4, 5, 0x8123, 7, 8])

count = message.seek_message_start_all_wrap(w, 8)
print "result:", count


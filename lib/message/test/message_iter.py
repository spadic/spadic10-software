#!/usr/bin/env python

from message_wrap import Message

class MessageIterator:
    def __init__(self):
        self.reset()

    def __call__(self, words):
        buf = self.buf + words
        m = self.m or Message()
        while buf:
            n = m.read_from_buffer(buf)
            if not m.is_complete:
                break
            yield m
            buf = buf[n:]
            m = Message()
        self.buf = buf
        self.m = m

    def reset(self):
        self.buf = []
        self.m = None

def iter_all(buffers, message_iter):
    messages = []
    for buf in buffers:
        messages += message_iter(buf)
    return messages

if __name__=='__main__':
    import sys
    mi = MessageIterator()
    buffers = [[
        0x8987,
        0x9654,
        0xA010,
        0xB075,
        0x8ABC,
        ], [
        0x9DEF,
        0xA020,
        0x0600,
        0xB0A3
    ]]
    for m in iter_all(buffers, mi):
        print m.as_text()

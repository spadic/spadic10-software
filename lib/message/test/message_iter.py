#!/usr/bin/env python


class MessageIterator:
    def __init__(self):
        self.buf = []
        self.m = None

    def __call__(self, words):
        buf = self.buf + words
        m = self.m or Message()
        while buf:
            n = m.read_from_buffer(buf)
            if not m.is_complete():
                break
            yield m
            buf = buf[n:]
            m = Message()
        self.buf = buf
        self.m = m
if __name__=='__main__':
    import sys
    mi = MessageIterator()
    words = [int(x, 16) for x in sys.stdin
             if x.strip() and not x.startswith('#')]
    for (i, m) in enumerate(mi(words)):
        print i, m.as_text()

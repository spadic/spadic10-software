#!/usr/bin/env python

def message_iter(words):
    buf = words
    m = Message()
    while buf:
        n = m.read_from_buffer(buf)
        if not n:
            break
        buf = buf[n:]
        if not m.is_complete():
            continue
        yield m
        m = Message()

if __name__=='__main__':
    import sys
    words = [int(x, 16) for x in sys.stdin
             if x.strip() and not x.startswith('#')]
    for (i, m) in enumerate(message_iter(words)):
        print i, m

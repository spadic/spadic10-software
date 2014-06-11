#!/usr/bin/env python

from message_wrap import Message

#---- implement this as C library -----------------------------------

class MessageIterator:
    def __init__(self):
        self.reset()

    def __call__(self, words):
        buf = words
        m = self.m or Message()
        while buf:
            n = m.read_from_buffer(buf)
            buf = buf[n:]
            if m.is_complete:
                yield m
                m = Message()
        self.m = m

    def reset(self):
        self.m = None

#--------------------------------------------------------------------

def iter_all(buffers, message_iter):
    messages = []
    for buf in buffers:
        messages += message_iter(buf)
    return messages

def as_text(message):
    s = []
    if message.is_hit:
        s.append("hit message")
        s.append("group ID: 0x%X  channel ID: 0x%X" % (
                 message.group_id, message.channel_id))
        s.append("timestamp: 0x%X" % message.timestamp)
        if message.samples is None:
            s.append("samples: invalid")
        else:
            s.append("samples (%d): %s" % (
                     len(message.samples), str(message.samples)))
        s.append("hit type: %d  stop type: %d" % (
                 message.hit_type, message.stop_type))
        return '\n'.join(s) + '\n'

    else:
        return "other message\n"

if __name__=='__main__':
    import sys
    mi = MessageIterator()
    buffers = [[
        0x9000,
        0xA000,
        0xB000,
        ], [
        0x8987,
        0x9654,
        0xA010,
        0xB075,
        0x8ABC,
        ], [
        0x9DEF,
        0xA020,
        0x0600,
        0xB0A3,
    ]]
    for m in iter_all(buffers, mi):
        print as_text(m)

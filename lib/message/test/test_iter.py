#!/usr/bin/env python

import unittest
from message_iter import MessageIterator

def split_at(n, words):
    return [words[:n], words[n:]]

class MessageIterBase(unittest.TestCase):
    def setUp(self):
        self.it = MessageIterator()
        self.words = [[
            0x8987,
            0x9654,
            0xA010,
            0xB075,
            ], [
            0x8ABC,
            0x9DEF,
            0xA020,
            0x0600,
            0xB0A3
        ]]

    def test_messages(self):
        messages = [m for w in self.words
                      for m in self.it(w)]
        self.assertEqual(len(messages), 2)
        for i, m in enumerate(messages):
            self.assertTrue(m.is_complete)
            self.assertTrue(m.is_hit)
            self.assertEqual(m.group_id, [0x98, 0xAB][i])
            self.assertEqual(m.channel_id, [0x7, 0xC][i])
            self.assertEqual(m.timestamp, [0x654, 0xDEF][i])
            self.assertEqual(m.samples, [[2], [4, 3]][i])
            self.assertEqual(m.hit_type, [3, 2][i])
            self.assertEqual(m.stop_type, [5, 3][i])

class MessageIterJoined(MessageIterBase):
    def setUp(self):
        MessageIterBase.setUp(self)
        w = self.words
        self.words = [sum(w, [])]

class MessageIterSplitFirst(MessageIterBase):
    def setUp(self):
        MessageIterBase.setUp(self)
        w = self.words
        (a, b), c = split_at(2, w[0]), w[1]
        self.words = [a, b + c]

class MessageIterSplitSecond(MessageIterBase):
    def setUp(self):
        MessageIterBase.setUp(self)
        w = self.words
        a, (b, c) = w[0], split_at(2, w[1])
        self.words = [a + b, c]

class MessageIterPrependEnd(MessageIterBase):
    def setUp(self):
        MessageIterBase.setUp(self)
        self.words.insert(0, [0x9000, 0xA000, 0xB000])

class MessageIterAppendStart(MessageIterBase):
    def setUp(self):
        MessageIterBase.setUp(self)
        self.words.append([0x8000, 0x9000, 0xA000])

if __name__=='__main__':
    unittest.main()

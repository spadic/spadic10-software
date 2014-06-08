#!/usr/bin/env python

import unittest
from message_wrap import Message

class MessageTestCase(unittest.TestCase):
    def setUp(self):
        self.m = Message()

class MessageNew(MessageTestCase):
    """
    Test properties of a newly created Message.
    """
    def test_complete(self):
        self.assertFalse(self.m.is_complete)

    def test_valid(self):
        self.assertFalse(self.m.is_valid)

    def test_hit(self):
        self.assertFalse(self.m.is_hit)

    def test_hit_aborted(self):
        self.assertFalse(self.m.is_hit_aborted)

    def test_buffer_overflow(self):
        self.assertFalse(self.m.is_buffer_overflow)

    def test_epoch_marker(self):
        self.assertFalse(self.m.is_epoch_marker)

    def test_epoch_out_of_sync(self):
        self.assertFalse(self.m.is_epoch_out_of_sync)

    def test_info(self):
        self.assertFalse(self.m.is_info)

    def test_samples(self):
        self.assertIsNone(self.m.samples)

class MessageNewReset(MessageNew):
    """
    Message after reset must have the same properties as a new one.
    """
    def setUp(self):
        MessageNew.setUp(self)
        self.m.reset()

class MessageHitBase(MessageNew):
    """
    Test properties of a simple hit message.
    """
    def setUp(self):
        MessageTestCase.setUp(self)
        self.m.read_from_buffer([
            0x8000,
            0x9000,
            0xA000,
            0xB000
        ])

    def test_complete(self):
        self.assertTrue(self.m.is_complete)

    def test_valid(self):
        self.assertTrue(self.m.is_valid)

    def test_hit(self):
        self.assertTrue(self.m.is_hit)

    def test_samples(self):
        pass # would fail because [] is not None

class MessageHitNoSamples(MessageHitBase):
    """
    Message with no samples.
    """
    def test_samples(self):
        self.assertEqual(self.m.samples, [])

class MessageHitValidSamples(MessageHitBase):
    """
    Test values contained in a hit message where the samples are valid.
    """
    def setUp(self):
        MessageTestCase.setUp(self)
        self.m.read_from_buffer([
            0x8ABC,
            0x9DEF,
            0xA008,
            0x0400,
            0xB0B5
        ])

    def test_group_id(self):
        self.assertEqual(self.m.group_id, 0xAB)

    def test_channel_id(self):
        self.assertEqual(self.m.channel_id, 0xC)

    def test_timestamp(self):
        self.assertEqual(self.m.timestamp, 0xDEF)

    def test_stop_type(self):
        self.assertEqual(self.m.stop_type, 0x5)

    def test_hit_type(self):
        self.assertEqual(self.m.hit_type, 0x3)

    def test_samples(self):
        self.assertEqual(self.m.samples, [1, 2])

class MessageHitInvalidSamples(MessageHitBase):
    """
    Hit message with fewer contained samples than indicated.
    """
    def setUp(self):
        MessageTestCase.setUp(self)
        self.m.read_from_buffer([
            0x8000,
            0x9000,
            0xA000,
            0xB100
        ])

    def test_samples(self):
        self.assertIsNone(self.m.samples)
    
if  __name__=='__main__':
    unittest.main()

#!/usr/bin/python

import ftdi

VID = 0x0403;
PID = 0x6010;

class LCD:
    def __init__(self, debug=False):
        self.ftdic = ftdi.ftdi_context()
        if debug:
            print 'ftdi_context():', ftdi.ftdi_get_error_string(self.ftdic)
        ftdi.ftdi_init(self.ftdic)
        if debug:
            print 'ftdi_init():', ftdi.ftdi_get_error_string(self.ftdic)
        ftdi.ftdi_usb_open(self.ftdic, VID, PID)
        if debug:
            print 'ftdi_usb_open():', ftdi.ftdi_get_error_string(self.ftdic)
        ftdi.ftdi_set_bitmode(self.ftdic, 0, ftdi.BITMODE_SYNCFF)
        if debug:
            print 'ftdi_set_bitmode():', ftdi.ftdi_get_error_string(self.ftdic)

    def _test_binary(self, name, value):
        if value not in [0, 1]:
            raise ValueError('%s must be 0 or 1' % name)

    def _send_instruction(self, RS, data, debug=False):
        self._test_binary('RS', RS)
        if data not in range(0x100):
            raise ValueError('data must be an integer between 0x00 and 0xFF')
        ftdi.ftdi_write_data(self.ftdic, chr(RS), 1)
        if debug:
            print 'ftdi_write_data():', ftdi.ftdi_get_error_string(self.ftdic)
        ftdi.ftdi_write_data(self.ftdic, chr(data), 1)
        if debug:
            print 'ftdi_write_data():', ftdi.ftdi_get_error_string(self.ftdic)

    def _instruction_table(self, table):
        if table not in range(3):
            raise ValueError('table must be an integer between 0 and 2')
        self._send_instruction(0, 0x28 + table)

    def write(self, string):
        for c in string:
            self._send_instruction(1, ord(c))

    def clear(self):
        self._send_instruction(0, 0x01)

    def home(self):
        self._send_instruction(0, 0x02)

    def cursor_pos(self, pos):
        if pos not in range(0x30):
            raise ValueError('pos must be an integer between 0x00 and 0x2F')
        self._send_instruction(0, 0x80+pos)

    def entry_mode(self, direction, shift):
        self._test_binary('direction', direction)
        self._test_binary('shift', shift)
        self._send_instruction(0, 4 + direction*2 + shift)

    def shift_cursor(self, count):
        direction = (count > 0)
        for i in range(abs(int(count))):
            self._send_instruction(0, 0x10 + direction*4)

    def shift_display(self, count):
        direction = (count > 0)
        for i in range(abs(int(count))):
            self._send_instruction(0, 0x18 + direction*4)

    def display_on_off(self, display, cursor, blink):
        self._test_binary('display', display)
        self._test_binary('cursor', cursor)
        self._test_binary('blink', blink)
        self._send_instruction(0, 8 + display*4 + cursor*2 + blink)

    def contrast(self, contrast):
        if contrast not in range(64):
            raise ValueError('contrast must be an integer between 0 and 63')
        self._instruction_table(1)
        self._send_instruction(0, 0x54 + (contrast >> 4))
        self._send_instruction(0, 0x70 + (contrast & 0x0F))
        self._instruction_table(0)

if __name__=='__main__':
    l = LCD()
    l.clear()
    l.home()
    l.write('SuSibo')


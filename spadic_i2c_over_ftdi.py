#!/usr/bin/python

import sys
import ftdi
# http://www.intra2net.com/en/developer/libftdi/documentation/group__libftdi.html

from spadic_rf import spadic_rf


def int2bytes(x, n=4):
    return [(x % (0x100 ** (i+1))) / (0x100 ** i) for i in range(n)]
    # int2bytes(x, 3) == [a0, a1, a2] --> x == a0 + a1*256 + a2*256**2


class SpadicI2cRf:
    def __init__(self):
        self._connect()

    def __del__(self):
        ftdi.ftdi_usb_close(self.ftdic)

    def _connect(self, VID=0x0403, PID=0x6010):
        context = ftdi.ftdi_context()
        ftdi.ftdi_init(context)
        if not (ftdi.ftdi_usb_open(context, VID, PID) == 0):
            self.ftdic = None
        else:
            ftdi.ftdi_set_bitmode(context, 0, ftdi.BITMODE_SYNCFF)
            self.ftdic = context

    def _write_data(self, byte_list):
        bytes_left = byte_list
        while bytes_left:
            num_bytes_written = ftdi.ftdi_write_data(self.ftdic,
                                ''.join(map(chr, bytes_left)), len(bytes_left))
            bytes_left = bytes_left[num_bytes_written:]

    def _read_data(self, num_bytes):
        buf = chr(0)*num_bytes
        bytes_read = []
        while buf:
            num_bytes_read = ftdi.ftdi_read_data(self.ftdic, buf, len(buf))
            bytes_read += map(ord, buf[:num_bytes_read])
            buf = buf[num_bytes_read:]
        return map(ord, buf)

    def write_register(self, address, data, iom_wr=0x01, iom_addr=0x20):
        iom_payload = int2bytes(address, 3) + int2bytes(data, 8)
        iom_len  = len(iom_payload) # == 11
        iom_header = [iom_wr, iom_addr, iom_len]
        self._write_data(iom_header + iom_payload)

    def read_register(self, address):
        self._write_data(address)
        return self._read_data(8)


if __name__=='__main__':
    if len(sys.argv < 3):
        sys.exit('usage: %s <reg_addr> <value>' % sys.argv[0])

    address = int(sys.argv[1], 16)
    value = int(sys.argv[2], 16)

    s = SpadicI2cRf()

    if s.ftdic is None:
        sys.exit('could not connect to device!')

    print 'connected!'

    # try to switch some LEDs on
    #s.write_register(spadic_rf['overrides'].address, 0xff)

    s.write_register(address, value)

    del s # _should_ be called automatically
    print 'disconnected!'


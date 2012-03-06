#!/usr/bin/python

import sys
import ftdi
# http://www.intra2net.com/en/developer/libftdi/documentation/group__libftdi.html

class FtdiOpenError(Exception):
    pass

class SpadicI2cRf:
    def __init__(self):
        self.ftdic = self._connect()

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


if __name__=='__main__':
    s = SpadicI2cRf()

    if s.ftdic is None:
        sys.exit('could not connect to device!')
    


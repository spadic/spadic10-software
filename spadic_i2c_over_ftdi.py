#!/usr/bin/python

import ftdi
# http://www.intra2net.com/en/developer/libftdi/documentation/group__libftdi.html
#import usb

VID = 0x0403;
PID = 0x6010;

class SPADIC_I2C_RF:
    def __init__(self):
        self.ftdic = ftdi.ftdi_context()
        ftdi.ftdi_init(self.ftdic)
        ftdi.ftdi_usb_open(self.ftdic, VID, PID)
        ftdi.ftdi_set_bitmode(self.ftdic, 0, ftdi.BITMODE_SYNCFF)

    def _write_data(self, byte_list):
        ftdi.ftdi_write_data(self.ftdic, ''.join(map(chr, byte_list)),
                             len(byte_list))

    def _read_data(self, num_bytes):
        buf = chr(0)*num_bytes
        ftdi.ftdi_read_data(self.ftdic, buf, num_bytes))
        return map(ord, buf)


if __name__=='__main__':
    s = SPADIC_I2C_RF()


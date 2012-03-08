#!/usr/bin/python

import sys
import ftdi
# http://www.intra2net.com/en/developer/libftdi/documentation/group__libftdi.html

from spadic_rf import spadic_rf
from spadic_sr import SR_LENGTH, SpadicShiftRegister


#--------------------------------------------------------------------
# dictionary of known ftdi error codes
#--------------------------------------------------------------------
ftdi_error_code = {
  -110: 'timeout',
  -666: 'device unavailable'
}


#--------------------------------------------------------------------
# convert data between various representations
#--------------------------------------------------------------------

def int2bitstring(x):
    return bin(x)[2:]
    # reverse: b = int2bitstring(x)
    #      --> x = int(b, 2)

def int2bytelist(x, n=4):
    return [(x >> (8*i)) % 0x100 for i in range(n)]
    # reverse: b = int2bytelist(x, n)
    #      --> x = sum(bi << (8*i) for (i, bi) in enumerate(b)


#--------------------------------------------------------------------
# FTDI -> IO Manager -> I2C -> SPADIC Register File communication
#--------------------------------------------------------------------

class SpadicI2cRf:
    #----------------------------------------------------------------
    # open/close USB connection with constructor/destructor methods
    #----------------------------------------------------------------
    def __init__(self, VID=0x0403, PID=0x6010):
        context = ftdi.ftdi_context()
        ftdi.ftdi_init(context)
        if not (ftdi.ftdi_usb_open(context, VID, PID) == 0):
            self.ftdic = None
            raise IOError('could not open USB connection!')
        ftdi.ftdi_set_bitmode(context, 0, ftdi.BITMODE_SYNCFF)
        self.ftdic = context

    def __del__(self):
        if self.ftdic is not None:
            ftdi.ftdi_usb_close(self.ftdic)

    #----------------------------------------------------------------
    # low-level communication
    #----------------------------------------------------------------
    def _write(self, byte_list):
        bytes_left = byte_list
        while bytes_left:
            n = ftdi.ftdi_write_data(self.ftdic,
                    ''.join(map(chr, bytes_left)), len(bytes_left))
            if n < 0:
                raise IOError('USB write error (error code %i: %s)'
                              % (n, ftdi_error_code[n]
                                    if n in ftdi_error_code else 'unknown'))
            bytes_left = bytes_left[n:]

    def _read(self, num_bytes):
        buf = chr(0)*num_bytes
        bytes_read = []
        while buf:
            num_bytes_read = ftdi.ftdi_read_data(self.ftdic, buf, len(buf))
            bytes_read += map(ord, buf[:num_bytes_read])
            buf = buf[num_bytes_read:]
        return map(ord, buf)

    #----------------------------------------------------------------
    # register file communication
    #----------------------------------------------------------------
    def write_register(self, address, data, iom_wr=0x01, iom_addr=0x20):
        iom_payload = int2bytelist(address, 3) + int2bytelist(data, 8)
        iom_len  = len(iom_payload) # == 11
        iom_header = [iom_wr, iom_addr, iom_len]
        self._write(iom_header + iom_payload)

    def read_register(self, address):
        self._write(address)
        return self._read(8)

    #----------------------------------------------------------------
    # write bits (given as string) to shift register
    #----------------------------------------------------------------
    def write_shiftregister(self, bits):
        if len(bits) != SR_LENGTH:
            raise ValueError('number of bits must be %i!' % SR_LENGTH)
        if not all(b in '01' for b in bits):
            raise ValueError('bit string must contain only 0 and 1!')
        chain = '0'
        mode = '10' # write mode
        ctrl_bits = int2bitstring(SR_LENGTH)+chain+mode
        ctrl_data = int(ctrl_bits, 2) # should be 0x1242 for 584 bits
        self.write_register(spadic_rf['control'].address, ctrl_data)

        # divide bit string into 16 bit chunks
        while bits: # should iterate int(SR_LENGTH/16) times
            chunk = int(bits[-16:], 2) # take the last 16 bits
            bits = bits[:-16]          # remove the last 16 bits
            self.write_register(spadic_rf['data'].address, chunk)


if __name__=='__main__':
    #if len(sys.argv < 3):
    #    sys.exit('usage: %s <reg_addr> <value>' % sys.argv[0])

    #address = int(sys.argv[1], 16)
    #value = int(sys.argv[2], 16)

    s = SpadicI2cRf()

    # try to switch some LEDs on
    #s.write_register(spadic_rf['overrides'].address, 0xff)
    #s.write_register(address, value)

    s.write_shiftregister('1'*584)



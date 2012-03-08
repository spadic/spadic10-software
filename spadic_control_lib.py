import ftdi
# http://www.intra2net.com/en/developer/libftdi/documentation/group__libftdi.html

from spadic_registers import RF_MAP, SR_MAP, SR_LENGTH


#--------------------------------------------------------------------
# dictionary of known ftdi error codes
#--------------------------------------------------------------------
FTDI_ERROR_CODE = {
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
# FTDI -> IO Manager -> I2C -> SPADIC Register File access
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
                              % (n, FTDI_ERROR_CODE[n]
                                    if n in FTDI_ERROR_CODE else 'unknown'))
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
        self.write_register(RF_MAP['control'], ctrl_data)

        # divide bit string into 16 bit chunks
        while bits: # should iterate int(SR_LENGTH/16) times
            chunk = int(bits[-16:], 2) # take the last 16 bits
            bits = bits[:-16]          # remove the last 16 bits
            self.write_register(RF_MAP['data'], chunk)


#--------------------------------------------------------------------
# SPADIC Shift Register representation
#--------------------------------------------------------------------

class SpadicShiftRegister:
    def __init__(self):
        self.bits = ['0']*SR_LENGTH
        # bits[0] = MSB (on the left side, shifted last)
        # bits[-1] = LSB (on the right side, shifted first)

    def __str__(self):
        return ''.join(self.bits)

    def set_value(self, name, value):
        pos = SR_MAP[name]
        n = len(pos)
        # make string of length n, pad if shorter, cut if longer
        bitstring = int2bitstring(value).rjust(n, '0')[-n:]
        for (i, b) in enumerate(bitstring):
            self.bits[pos[i]] = b

    def get_value(self, name):
        return int(''.join([self.bits[p] for p in SR_MAP[name]]), 2)


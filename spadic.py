import signal

import iom
from bit_byte_helper import int2bitstring, int2bytelist


#====================================================================
# prepare timeout
#====================================================================
class TimeoutException(Exception):
    pass

# set timeout handler for SIGALRM to raise TimeoutException
def timeout_handler(signum, frame):
    raise TimeoutException()
signal.signal(signal.SIGALRM, timeout_handler)


#====================================================================
# constants
#====================================================================

#--------------------------------------------------------------------
# IO Manager addresses
#--------------------------------------------------------------------
IOM_ADDR_I2C = 0x20
IOM_ADDR_TDA = 0x30

# size of package parts in IOM package mode
# first byte is always 0xFF --> discard after read
PACKAGE_SIZE = 9


#====================================================================
# FTDI -> IO Manager -> SPADIC communication
#====================================================================

class Spadic(iom.FtdiIom):
    #----------------------------------------------------------------
    # register file access
    #----------------------------------------------------------------
    def write_register(self, address, data):
        iom_payload = int2bytelist(address, 3) + int2bytelist(data, 8)
        self._iom_write(IOM_ADDR_I2C, iom_payload)

    def read_register(self, address):
        i2c_read_implemented = False # TODO fix i2c read
        if not i2c_read_implemented:
            raise NotImplementedError
        # write register address
        iom_payload = int2bytelist(address, 3)
        self._iom_write(IOM_ADDR_I2C, iom_payload)
        # read register value (always 64 bits)
        return self._iom_read(IOM_ADDR_I2C, 8)

    #----------------------------------------------------------------
    # write bits (given as string) to shift register
    #----------------------------------------------------------------
    def write_shiftregister(self, bits):
        if len(bits) != SR_LENGTH:
            raise ValueError('number of bits must be %i!' % SR_LENGTH)
        if not all(b in '01' for b in bits):
            raise ValueError('bit string must contain only 0 and 1!')
        chain = '0' # ?
        mode = '10' # write mode
        ctrl_bits = int2bitstring(SR_LENGTH)+chain+mode
        ctrl_data = int(ctrl_bits, 2) # should be 0x1242 for 584 bits
        self.write_register(RF_MAP['control'], ctrl_data)

        # divide bit string into 16 bit chunks
        while bits: # should iterate int(SR_LENGTH/16) times
            chunk = int(bits[-16:], 2) # take the last 16 bits
            bits = bits[:-16]          # remove the last 16 bits
            self.write_register(RF_MAP['data'], chunk)

    #----------------------------------------------------------------
    # read data from test output -> IOM -> FTDI
    # (assuming package mode is used)
    #----------------------------------------------------------------
    def read_data(self, num_bytes=None, timeout=1):
        # read data until num_bytes are read (None -> 'infinity')
        # abort if timeout is over after no data was received
        num_bytes_left = num_bytes
        while num_bytes is None or num_bytes_left >= PACKAGE_SIZE:
            if timeout is not None:
                signal.alarm(timeout) # set alarm
            try:
                bytes_read = self._ftdi_read(PACKAGE_SIZE)[1:]
                             # discard the first byte
            except TimeoutException:
                break
            finally:
                signal.alarm(0) # disable alarm in any case

            for byte in bytes_read:
                yield byte
            if num_bytes_left:
                num_bytes_left -= len(bytes_read)
            
    #----------------------------------------------------------------
    # write data to test FTDI -> IOM -> test input
    #----------------------------------------------------------------
    def write_data(self, data):
        if len(data) == 1:
            data.append(0) # test input interface needs at least 2 values
        self._iom_write(IOM_ADDR_TDA, [(x%512)>>1 for x in data])
            

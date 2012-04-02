from spadic_registers import RF_MAP, SR_MAP, SR_LENGTH
from bit_byte_helper import *


#====================================================================
# constants
#====================================================================

#--------------------------------------------------------------------
# IO Manager addresses
#--------------------------------------------------------------------
IOM_ADDR_I2C = 0x20
IOM_ADDR_TDO = 0x30


#====================================================================
# FTDI -> IO Manager -> SPADIC communication
#====================================================================

class Spadic(FtdiIom):
    #----------------------------------------------------------------
    # register file access
    #----------------------------------------------------------------
    def write_register(self, address, data):
        iom_payload = int2bytelist(address, 3) + int2bytelist(data, 8)
        self._iom_write(IOM_ADDR_I2C, iom_payload)

    def read_register(self, address):
        i2c_read_implemented = False # TODO fix i2c read
        if not i2c_read_implemented:
            print 'implement i2c read operation first!'
            return
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
    # read data from test output
    #----------------------------------------------------------------
    def read_data_test_output(self, num_bytes, block_size=255):
        num_bytes_left = num_bytes
        while num_bytes_left > 0: # negative numbers are treated as True
            bytes_read = self._iom_read(IOM_ADDR_TDO,
                                        min(num_bytes_left, block_size))
            for byte in bytes_read:
                yield byte
            num_bytes_left -= block_size
            

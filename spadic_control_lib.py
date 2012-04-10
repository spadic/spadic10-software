from iom_lib import *
from spadic_registers import *
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
    # write configuration from dictionary
    #----------------------------------------------------------------
    def config(self, rf_dict, sr_dict):
        for reg in rf_dict:
            self.write_register(RF_MAP[reg], rf_dict[reg])

        sr = SpadicShiftRegister()
        for reg in sr_dict:
            sr.set_value(reg, sr_dict[reg])
        self.write_shiftregister(str(sr))

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
            

# prepare some stuff that is frequently used
import time, random
s = Spadic()

def ledtest():
    s.write_register(RF_MAP['overrides'], 0x10)
    s.write_register(RF_MAP['overrides'], 0x00)

def testout(x):
    if x not in [0, 1]:
        raise ValueError('only 0 or 1 allowed!')
    s.write_register(RF_MAP['REG_enableTestOutput'], x)

def testin(x):
    if x not in [0, 1]:
        raise ValueError('only 0 or 1 allowed!')
    s.write_register(RF_MAP['REG_enableTestInput'], x)

def enablechannel0(x):
    if x not in [0, 1]:
        raise ValueError('only 0 or 1 allowed!')
    s.write_register(RF_MAP['REG_disableChannelA'], 2**16-1-x)
    s.write_register(RF_MAP['REG_disableChannelB'], 2**16-1)

def zerosr():
    sr = SpadicShiftRegister()
    s.write_shiftregister(str(sr))

def randdata(n):
    return [random.randint(0, 120) for i in range(n)]
    
def ftdireadtest(f=None):
    start = time.time()
    print >> f, ''
    while True:
        d = s._ftdi_read(9, 1)
        if len(d):
            print >> f, '%6.1f: ' % (time.time()-start) + \
                        ' '.join('%02X' % x for x in d)
    


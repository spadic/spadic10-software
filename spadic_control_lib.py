import signal
import time

from bit_byte_helper import *
from iom_lib import *
from spadic_registers import *
from spadic_message_lib import *
from spadic_config import *


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

class Spadic(FtdiIom):
    #----------------------------------------------------------------
    # register file access (see below for special register methods)
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
    def configrf(self, rf_dict):
        for reg in rf_dict:
            self.write_register(RF_MAP[reg], rf_dict[reg])

    def configsr(self, sr_dict):
        sr = SpadicShiftRegister()
        for reg in sr_dict:
            sr.set_value(reg, sr_dict[reg])
        self.write_shiftregister(str(sr))

    def config(self, rf_dict, sr_dict):
        self.configrf(rf_dict)
        self.configsr(sr_dict)

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
        s._iom_write(IOM_ADDR_TDA, [(x%512)>>1 for x in data])
            

    #================================================================
    # special register methods
    #================================================================
            
    #----------------------------------------------------------------
    # hit logic
    #----------------------------------------------------------------
    def threshold(self, threshold1, threshold2, diffmode=0):
        for (reg, th) in [('REG_threshold1', threshold1),
                          ('REG_threshold2', threshold2)]:
            if th < -256 or th > 255:
                raise ValueError('valid threshold range: -256..255')
            self.write_register(RF_MAP[reg], th % 512)
        self.write_register(RF_MAP['REG_compDiffMode'], diffmode)
        
    def selectmask(self, mask=0xFFFF0000, windowlength=16):
        if mask < 0 or mask > 0xFFFFFFFF:
            raise ValueError('expected 32 bit integer')
        mask_h = mask >> 16;
        mask_l = mask & 0xFFFF;
        self.write_register(RF_MAP['REG_selectMask_h'], mask_h)
        self.write_register(RF_MAP['REG_selectMask_l'], mask_l)
        if windowlength < 0 or windowlength > 63:
            raise ValueError('valid hit window length range: 0..63')
        self.write_register(RF_MAP['REG_hitWindowLength'], windowlength)
            
    #----------------------------------------------------------------
    # filter settings
    #----------------------------------------------------------------

    def _filter_enable(self, enable):
        if enable < 0 or enable > 0x1F:
            raise ValueError('expected 5 bit integer')
        self.write_register(RF_MAP['REG_bypassFilterStage'], ~enable)
        # enable scaling/offset:     0x10
        # enable first filter stage: 0x01

    def _filter_scale(self, scale, norm=False):
        if norm:
            scale = int(round(32*scale))
        if scale < -256 or scale > 255:
            raise ValueError('valid scaling range: -256..255')
        self.write_register(RF_MAP['REG_scalingFilter'], scale)

    def _filter_offset(self, offset):
        if offset < -256 or offset > 255:
            raise ValueError('valid offset range: -256..255')
        self.write_register(RF_MAP['REG_offsetFilter'], offset)

    def _filter_coeff_(self, coeff, norm, num, reg):
        if not len(coeff) == num:
            raise ValueError('expected list of %i coefficients' % num)
        if norm:
            coeff = [int(round(32*c)) for c in coeff]
        if any(c < -32 or c > 31 for c in coeff):
            raise ValueError('valid coefficient range: -32..31')
        value = sum(c%64 << 6*i for (i, c) in enumerate(coeff))
        value_h = value >> 16;
        value_l = value & 0xFFFF;
        self.write_register(RF_MAP[reg+'_h'], value_h)
        self.write_register(RF_MAP[reg+'_l'], value_l)

    def _filter_coeffa(self, coeff, norm=False):
        self._filter_coeff_(coeff, norm, 3, 'REG_aCoeffFilter')
    def _filter_coeffb(self, coeff, norm=False):
        self._filter_coeff_(coeff, norm, 4, 'REG_bCoeffFilter')

    def filter_settings(self, enable=None, scale=None, offset=None,
                        coeffa=None, coeffb=None, norm=False):
        if enable is None: enable = 0x00
        if scale is None: scale = 1.0 if norm else 32
        if offset is None: offset = 0
        if coeffa is None: coeffa = [0]*3
        if coeffb is None: coeffb = [0]*4
        self._filter_enable(enable)
        self._filter_scale(scale, norm)
        self._filter_offset(offset)
        self._filter_coeffa(coeffa, norm)
        self._filter_coeffb(coeffb, norm)

#--------------------------------------------------------------------
# prepare some stuff that is frequently used
#--------------------------------------------------------------------
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
    s.write_register(RF_MAP['REG_disableChannelA'], 0xFFFF-x)
    s.write_register(RF_MAP['REG_disableChannelB'], 0xFFFF)

def zerosr():
    sr = SpadicShiftRegister()
    s.write_shiftregister(str(sr))

def config_ftdireadtest():
    s.write_register(8, 0x10)
    zerosr()
    testin(1)
    testout(1)
    enablechannel0(1)
    s.selectmask(0xFFFF0000) # first 16 samples
    s.write_register(48, 0) # diffmode off
    s.write_register(8, 0x00)

def config_analogtest():
    s.write_register(8, 0x10)
    s.config(RF_DEFAULT, SR_DEFAULT)
    s.write_register(8, 0x00)

def randdata(n):
    return [random.randint(0, 120) for i in range(n)]
    
def ftdireadtest(f=None, max_timeout=1, timeout_init=1e-6):
    start = time.time()
    timeout = timeout_init
    print >> f, ''
    while True:
        d = s._ftdi_read(9, 1)
        if d:
            timeout = timeout_init
            print >> f, '%6.1f: ' % (time.time()-start) + \
                        ' '.join('%02X' % x for x in d)
        else:
            if timeout > max_timeout:
                break
            time.sleep(timeout)
            timeout = 2*timeout

def getmessages():
    for m in messages(message_words(s.read_data())):
        yield Message(m)

def quickwrite(data):
    for i in range(4):
        s.write_data(data)
        time.sleep(0.1)
    M = list(getmessages())
    if M:
        return M[-1].data
    else:
        print 'no messages found!'

def enableamp(channel, only=True):
  if only:
    for i in range(32):
        reg = 'enAmpP_' + str(i)
        SR_DEFAULT[reg] = 1 if (i == channel) else 0
    s.configsr(SR_DEFAULT)
  else:
    reg = 'enAmpP_' + str(channel)
    SR_DEFAULT[reg] = 1
    s.configsr(SR_DEFAULT)
    

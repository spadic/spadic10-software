import time

from spadic_registers import SpadicRegisterFile, SpadicShiftRegister
from spadic_config import *


class SpadicController:
    _registerfile = SpadicRegisterFile()
    _shiftregister = SpadicShiftRegister()

    def __init__(self, spadic):
        self._spadic = spadic

    #----------------------------------------------------------------
    # write configuration from dictionary
    #----------------------------------------------------------------
    def configrf(self, rf_dict):
        for reg in rf_dict:
            self.write_register(RF_MAP[reg], rf_dict[reg])

    def config(self, rf_dict, sr_dict):
        self.configrf(rf_dict)
        self.configsr(sr_dict)

            
            

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
    

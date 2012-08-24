from register import RegisterFile, ShiftRegister

#================================================================
# helper functions
#================================================================
        
#----------------------------------------------------------------
# filter settings
#----------------------------------------------------------------
def _filter_enable(enable):
    if enable < 0 or enable > 0x1F:
        raise ValueError('expected 5 bit integer')
    return {'REG_bypassFilterStage': ~enable}
    # enable scaling/offset:     0x10
    # enable first filter stage: 0x01

def _filter_scale(scale, norm=False):
    if norm:
        scale = int(round(32*scale))
    if scale < -256 or scale > 255:
        raise ValueError('valid scaling range: -256..255')
    return {'REG_scalingFilter': scale}

def _filter_offset(offset):
    if offset < -256 or offset > 255:
        raise ValueError('valid offset range: -256..255')
    return {'REG_offsetFilter': offset}

def _filter_coeff_(coeff, norm, num, reg):
    if not len(coeff) == num:
        raise ValueError('expected list of %i coefficients' % num)
    if norm:
        coeff = [int(round(32*c)) for c in coeff]
    if any(c < -32 or c > 31 for c in coeff):
        raise ValueError('valid coefficient range: -32..31')
    value = sum(c%64 << 6*i for (i, c) in enumerate(coeff))
    value_h = value >> 16;
    value_l = value & 0xFFFF;
    return {reg+'_h': value_h, reg+'_l': value_l} 

def _filter_coeffa(coeff, norm=False):
    return _filter_coeff_(coeff, norm, 3, 'REG_aCoeffFilter')
def _filter_coeffb(coeff, norm=False):
    return _filter_coeff_(coeff, norm, 4, 'REG_bCoeffFilter')


#================================================================
# Main controller unit
#================================================================
class Controller:
    """SPADIC configuration controller."""

    def __init__(self, spadic):
        self._spadic = spadic
        self.registerfile = RegisterFile(spadic)
        self.shiftregister = ShiftRegister(spadic)

    def leds(self, led1=False, led2=False):
        """Turn the userpin1/2 LEDs on or off."""
        value = ((0x10 if led1 else 0) +
                 (0x20 if led2 else 0))
        self.registerfile['overrides'] = value

    def write_shiftregister(self, config=None):
        """Perform the shift register write operation."""
        if config is not None:
            self.shiftregister.load(config)
        self.leds(1, 0)
        self.shiftregister.write()
        self.leds(0, 0)

    def clear_shiftregister(self):
        """Fill the shift register with zeros."""
        config = dict((name, 0) for name in self.shiftregister)
        self.write_shiftregister(config)

    def write_registerfile(self, config):
        """Write a configuration into the register file."""
        self.leds(1, 0)
        self.registerfile.load(config)
        self.leds(0, 0)

    def testdata(self, inp, out):
        if any(x not in [0, 1] for x in [inp, out]):
            raise ValueError('only 0 or 1 allowed!')
        config = {'REG_enableTestInput': inp,
                  'REG_enableTestOutput': out}
        self.write_registerfile(config)

    def comparator(self, threshold1, threshold2, diffmode=0):
        """Configure the digital comparators."""
        config = {}
        for (name, th) in [('REG_threshold1', threshold1),
                           ('REG_threshold2', threshold2)]:
            if th < -256 or th > 255:
                raise ValueError('valid threshold range: -256..255')
            config[name] = th % 512
        config['REG_compDiffMode'] = diffmode
        self.write_registerfile(config)
        
    def hitlogic(self, mask=0xFFFF0000, window=16):
        """Configure the hit logic."""
        if mask < 0 or mask > 0xFFFFFFFF:
            raise ValueError('expected 32 bit integer')
        config = {}
        mask_h = mask >> 16;
        mask_l = mask & 0xFFFF;
        config['REG_selectMask_h'] = mask_h
        config['REG_selectMask_l'] = mask_l
        if window < 0 or window > 63:
            raise ValueError('valid hit window length range: 0..63')
        config['REG_hitWindowLength'] = window
        self.write_registerfile(config)

    def filter(self, enable=None, scale=None, offset=None,
                     coeffa=None, coeffb=None, norm=False):
        """Configure the digital filters."""
        if enable is None: enable = 0x00
        if scale is None: scale = 1.0 if norm else 32
        if offset is None: offset = 0
        if coeffa is None: coeffa = [0]*3
        if coeffb is None: coeffb = [0]*4
        config = {}
        config.update(_filter_enable(enable))
        config.update(_filter_scale(scale, norm))
        config.update(_filter_offset(offset))
        config.update(_filter_coeffa(coeffa, norm))
        config.update(_filter_coeffb(coeffb, norm))
        self.write_registerfile(config)

#    def config(self, rf_dict, sr_dict):
#        self.configrf(rf_dict)
#        self.configsr(sr_dict)
#
#            
#            
#
##--------------------------------------------------------------------
## prepare some stuff that is frequently used
##--------------------------------------------------------------------
#import time, random
#s = Spadic()
#
#def config_analogtest():
#    s.write_register(8, 0x10)
#    s.config(RF_DEFAULT, SR_DEFAULT)
#    s.write_register(8, 0x00)
#
#def getmessages():
#    for m in messages(message_words(s.read_data())):
#        yield Message(m)
#
#def enableamp(channel, only=True):
#  if only:
#    for i in range(32):
#        reg = 'enAmpP_' + str(i)
#        SR_DEFAULT[reg] = 1 if (i == channel) else 0
#    s.configsr(SR_DEFAULT)
#  else:
#    reg = 'enAmpP_' + str(channel)
#    SR_DEFAULT[reg] = 1
#    s.configsr(SR_DEFAULT)
    

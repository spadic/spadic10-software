from register import RegisterFile, ShiftRegister

#================================================================
# helper functions
#================================================================
ONOFF = {1: 'ON', 0: 'OFF'}
        
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
# LED control
#================================================================
class Led:
    """Control unit for the userpin1/2 LEDs."""
    _userpin1 = 0
    _userpin2 = 0

    def __init__(self, registerfile):
        self._registerfile = registerfile

    def __call__(self, userpin1=None, userpin2=None):
        """Turn the userpin1/2 LEDs on or off."""
        if userpin1 is not None:
            self._userpin1 = 1 if userpin1 else 0
        if userpin2 is not None:
            self._userpin2 = 1 if userpin2 else 0
        value = ((0x10 * self._userpin1) +
                 (0x20 * self._userpin2))
        self._registerfile['overrides'] = value

    def reset(self):
        self(0, 0)

    def __str__(self):
        return ('userpin1: %s  userpin2: %s' %
                (ONOFF[self._userpin1], ONOFF[self._userpin2]))
        

#================================================================
# Test data control
#================================================================
class TestData:
    """Control unit for the test data input and output."""
    _testdatain = 0
    _testdataout = 0

    def __init__(self, registerfile):
        self._registerfile = registerfile

    def __call__(self, testdatain=None, testdataout=None):
        """Turn the test data input and output on or off."""
        if testdatain is not None:
            self._testdatain = 1 if testdatain else 0
        if testdataout is not None:
            self._testdataout = 1 if testdataout else 0
        self._registerfile['REG_enableTestInput'] = self._testdatain
        self._registerfile['REG_enableTestOutput'] = self._testdataout

    def reset(self):
        self(0, 0)

    def __str__(self):
        return ('test data input: %s  test data output: %s' %
                (ONOFF[self._testdatain], ONOFF[self._testdataout]))


#================================================================
# Comparator control
#================================================================
class Comparator:
    """Control unit for the digital comparators."""
    _threshold1 = 0
    _threshold2 = 0
    _diffmode = 0

    def __init__(self, registerfile):
        self._registerfile = registerfile

    def __call__(self, threshold1=None, threshold2=None, diffmode=None):
        """Set the two thresholds and turn the diff mode on or off."""
        thresholds_to_check = [th for th in [threshold1, threshold2]
                               if th is not None]
        if any(th < -256 or th > 255 for th in thresholds_to_check):
            raise ValueError('valid threshold range: -256..255')
        if threshold1 is not None:
            self._threshold1 = threshold1
        if threshold2 is not None:
            self._threshold2 = threshold2
        if diffmode is not None:
            self._diffmode = 1 if diffmode else 0
        self._registerfile['REG_threshold1'] = self._threshold1 % 512
        self._registerfile['REG_threshold2'] = self._threshold2 % 512
        self._registerfile['REG_compDiffMode'] = self._diffmode

    def reset(self):
        self(0, 0, 0)

    def __str__(self):
        return ('threshold 1: %i  threshold 2: %i\ndiff mode: %s' %
                (self._threshold1, self._threshold2, ONOFF[self._diffmode]))


#================================================================
# Main control
#================================================================
class Controller:
    """SPADIC configuration controller."""

    def __init__(self, spadic):
        self._spadic = spadic
        self.registerfile = RegisterFile(spadic)
        self.shiftregister = ShiftRegister(spadic)
        self.led = Led(self.registerfile)
        self.testdata = TestData(self.registerfile)
        self.comparator = Comparator(self.registerfile)

    def write_shiftregister(self, config=None):
        """Perform the shift register write operation."""
        if config is not None:
            self.shiftregister.load(config)
        self.led(1)
        self.shiftregister.write()
        self.led(0)

    def clear_shiftregister(self):
        """Fill the shift register with zeros."""
        config = dict((name, 0) for name in self.shiftregister)
        self.write_shiftregister(config)

    def write_registerfile(self, config):
        """Write a configuration into the register file."""
        self.led(1)
        self.registerfile.load(config)
        self.led(0)

    def save(self, f=None, nonzero=True):
        """Save the current configuration to a text file."""
        def frame(title, symbol='=', width=60):
            return ['#' + symbol*(width-1),
                    '# '+title,
                    '#' + symbol*(width-1), '']
        def fmtnumber(n, sz):
            if sz == 1:
                fmt = '{0}'
            else:
                nhex = sz//4 + (1 if sz%4 else 0)
                fmt = '0x{:0'+str(nhex)+'X}'
            return fmt.format(n).rjust(6)
        lines = frame('Register file')
        rflines = []
        for name in self.registerfile.dict(nonzero):
            ln = name.ljust(25) + ' '
            sz = self.registerfile.size(name)
            ln += fmtnumber(self.registerfile[name], sz)
            rflines.append(ln)
        lines += sorted(rflines, key=str.lower)
        lines.append('')
        lines += frame('Shift register')
        srlines = []
        for name in self.shiftregister.dict(nonzero):
            ln = name.ljust(25) + ' '
            sz = self.shiftregister.size(name)
            ln += fmtnumber(self.shiftregister[name], sz)
            srlines.append(ln)
        lines += sorted(srlines, key=str.lower)
        print >> f, '\n'.join(lines)
        
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
    

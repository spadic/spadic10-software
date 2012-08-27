from register import RegisterFile, ShiftRegister

#================================================================
# helper functions
#================================================================
def onoff(value):
    return 'ON' if value else 'OFF'

def frame(title, symbol='=', width=60):
    return '\n'.join(['#' + symbol*(width-1),
                      '# '+title,
                      '#' + symbol*(width-1)])


#================================================================
# LEDs
#================================================================
_LED_USERPIN1 = 0
_LED_USERPIN2 = 0
class Led:
    """Controls the userpin1/2 LEDs."""
    def __init__(self, registerfile):
        self._registerfile = registerfile
        self.reset()

    def reset(self):
        self(_LED_USERPIN1, _LED_USERPIN2)

    def __call__(self, userpin1=None, userpin2=None):
        """Turn the userpin1/2 LEDs on or off."""
        if userpin1 is not None:
            self._userpin1 = 1 if userpin1 else 0
        if userpin2 is not None:
            self._userpin2 = 1 if userpin2 else 0
        value = ((0x10 * self._userpin1) +
                 (0x20 * self._userpin2))
        self._registerfile['overrides'] = value

    def __str__(self):
        return ('userpin1: %s  userpin2: %s' %
                (onoff(self._userpin1), onoff(self._userpin2)))
        

#================================================================
# Test data
#================================================================
_TESTDATAIN = 0
_TESTDATAOUT = 0
class TestData:
    """Controls the test data input and output."""
    def __init__(self, registerfile):
        self._registerfile = registerfile
        self.reset()

    def reset(self):
        self(_TESTDATAIN, _TESTDATAOUT)

    def __call__(self, testdatain=None, testdataout=None):
        """Turn the test data input and output on or off."""
        if testdatain is not None:
            self._testdatain = 1 if testdatain else 0
        if testdataout is not None:
            self._testdataout = 1 if testdataout else 0
        self._registerfile['REG_enableTestInput'] = self._testdatain
        self._registerfile['REG_enableTestOutput'] = self._testdataout

    def __str__(self):
        return ('test data input: %s  test data output: %s' %
                (onoff(self._testdatain), onoff(self._testdataout)))


#================================================================
# Comparator
#================================================================
_CMP_TH1 = 0
_CMP_TH2 = 0
_CMP_DIFFMODE = 0
class Comparator:
    """Controls the digital comparators."""
    def __init__(self, registerfile):
        self._registerfile = registerfile
        self.reset()

    def reset(self):
        self(_CMP_TH1, _CMP_TH2, _CMP_DIFFMODE)

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

    def __str__(self):
        return ('threshold 1: %i  threshold 2: %i  diff mode: %s' %
                (self._threshold1, self._threshold2, onoff(self._diffmode)))
        

#================================================================
# Hit logic
#================================================================
_HITLOGIC_MASK = 0xFFFF0000
_HITLOGIC_WINDOW = 16
class HitLogic:
    """Controls the hit logic."""
    def __init__(self, registerfile):
        self._registerfile = registerfile
        self.reset()

    def reset(self):
        self(_HITLOGIC_MASK, _HITLOGIC_WINDOW)

    def __call__(self, mask=None, window=None):
        """Set the selection mask and the hit window length."""
        if mask is not None:
            if mask < 0 or mask > 0xFFFFFFFF:
                raise ValueError('valid mask range: 0..0xFFFFFFFF')
            self._mask = mask
        if window is not None:
            if window < 0 or window > 63:
                raise ValueError('valid hit window length range: 0..63')
            self._window = window

        mask_h = self._mask >> 16;
        mask_l = self._mask & 0xFFFF;
        self._registerfile['REG_selectMask_h'] = mask_h
        self._registerfile['REG_selectMask_l'] = mask_l
        self._registerfile['REG_hitWindowLength'] = self._window

    def __str__(self):
        return ('selection mask: 0x%08X  hit window length: %i' %
                (self._mask, self._window))
        
#================================================================
# Filter
#================================================================
_FILTER_COEFFA = 0
_FILTER_COEFFB = 0
_FILTER_ENABLE = 0
_FILTER_SCALING = 0
_FILTER_OFFSET = 0

#----------------------------------------------------------------
# Single stage
#----------------------------------------------------------------
class Stage:
    """Controls a filter stage."""
    def __init__(self, registerfile, coeffa_list, coeffb_list,
                                                  enable_list, position):
        self._registerfile = registerfile
        self._coeffa = coeffa_list
        self._coeffb = coeffb_list
        self._enable = enable_list
        self._position = position
        self.reset()

    def reset(self):
        self(_FILTER_COEFFA, _FILTER_COEFFB, _FILTER_ENABLE)

    def __call__(self, coeffa=None, coeffb=None, enable=None, norm=False):
        """Set the 'a'/'b' coefficients and turn the stage on or off."""
        coeff_to_check = [c for c in [coeffa, coeffb] if c is not None]
        coeff_max = 0.96875 if norm else 31
        coeff_min = -1 if norm else -32
        if any(c < coeff_min or c > coeff_max for c in coeff_to_check):
            raise ValueError('valid coefficient range: %s..%s' %
                             (str(coeff_min), str(coeff_max)))
        if coeffa is not None:
            self._coeffa[self._position] = (coeffa if not norm
                                            else int(round(32*coeffa)))
        if coeffb is not None:
            self._coeffb[self._position] = (coeffb if not norm
                                            else int(round(32*coeffb)))
        if enable is not None:
            self._enable[self._position] = 1 if enable else 0

        value_a = sum(c%64 << 6*i for (i, c) in enumerate(self._coeffa)) >> 6
        value_b = sum(c%64 << 6*i for (i, c) in enumerate(self._coeffb))
        self._registerfile['REG_aCoeffFilter_h'] = value_a >> 16
        self._registerfile['REG_aCoeffFilter_l'] = value_a & 0xFFFF
        self._registerfile['REG_bCoeffFilter_h'] = value_b >> 16
        self._registerfile['REG_bCoeffFilter_l'] = value_b & 0xFFFF
        value_enable = sum(en << i for (i, en) in enumerate(self._enable))
        self._registerfile['REG_bypassFilterStage'] = (~value_enable) % 32

    def __str__(self):
        p = self._position
        return ('coeff. a: %4i  coeff. b: %4i  enabled: %s' %
                (self._coeffa[p], self._coeffb[p], onoff(self._enable[p])))

#----------------------------------------------------------------
# Single stage (half)
#----------------------------------------------------------------
class StageZero(Stage):
    """Controls a half stage which has no 'a' coefficient."""

    def __call__(self, coeffb=None, enable=None, norm=False):
        """Set the 'b' coefficient and turn the stage on or off."""
        Stage.__call__(self, None, coeffb, enable, norm)

    def __str__(self):
        p = self._position
        return ('coeff. a:  ---  coeff. b: %4i  enabled: %s' %
                (self._coeffb[p], onoff(self._enable[p])))

#----------------------------------------------------------------
# Scaling/offset
#----------------------------------------------------------------
class ScalingOffset:
    """Controls a scaling/offset stage."""
    def __init__(self, registerfile, enable_list, position):
        self._registerfile = registerfile
        self._enable = enable_list
        self._position = position
        self.reset()

    def reset(self):
        self(_FILTER_SCALING, _FILTER_OFFSET, _FILTER_ENABLE)

    def __call__(self, scaling=None, offset=None, enable=None, norm=False):
        """Set the scaling and offset and turn the stage on or off."""
        if scaling is not None:
            scaling_min = -8 if norm else -256
            scaling_max = 7.96875 if norm else 255
            if scaling < scaling_min or scaling > scaling_max:
                raise ValueError('valid scaling range: -%s..%s' %
                                 (str(scaling_min), str(scaling_max)))
            self._scaling = (scaling if not norm
                             else int(round(32*scaling)))
        if offset is not None:
            if offset < -256 or offset > 255:
                raise ValueError('valid offset range: -256..255')
            self._offset = offset
        if enable is not None:
            self._enable[self._position] = 1 if enable else 0

        self._registerfile['REG_offsetFilter'] = self._offset
        self._registerfile['REG_scalingFilter'] = self._scaling
        value_enable = sum(en << i for (i, en) in enumerate(self._enable))
        self._registerfile['REG_bypassFilterStage'] = (~value_enable) % 32

    def __str__(self):
        p = self._position
        return ('scaling: %5i  offset: %6i  enabled: %s' %
                (self._scaling, self._offset, onoff(self._enable[p])))

#----------------------------------------------------------------
# Whole filter
#----------------------------------------------------------------
class Filter:
    """Collection of several filter stages."""
    def __init__(self, registerfile):
        self._registerfile = registerfile
        self._coeffa = [_FILTER_COEFFA for _ in range(4)]
        self._coeffb = [_FILTER_COEFFB for _ in range(4)]
        self._enable = [_FILTER_ENABLE for _ in range(5)]
        self.stage = [StageZero(self._registerfile, self._coeffa,
                                self._coeffb, self._enable, 0),
                      Stage(self._registerfile, self._coeffa,
                                self._coeffb, self._enable, 1),
                      Stage(self._registerfile, self._coeffa,
                                self._coeffb, self._enable, 2),
                      Stage(self._registerfile, self._coeffa,
                                self._coeffb, self._enable, 3),
                      ScalingOffset(self._registerfile, self._enable, 4)]
        self.reset()

    def reset(self):
        for s in self.stage:
            s.reset()

    def __str__(self):
        return '\n'.join(('Stage %i: ' % i) + str(s)
                         for (i, s) in enumerate(self.stage))


#================================================================
# Main control
#================================================================
class Controller:
    """SPADIC configuration controller."""

    def __init__(self, spadic):
        self._spadic = spadic
        self.registerfile = RegisterFile(spadic)
        self.shiftregister = ShiftRegister(spadic)

        # add control units
        self._units = {}
        self.led = Led(self.registerfile)
        self._units['LEDs'] = self.led
        self.testdata = TestData(self.registerfile)
        self._units['Test data'] = self.testdata
        self.comparator = Comparator(self.registerfile)
        self._units['Comparator'] = self.comparator
        self.hitlogic = HitLogic(self.registerfile)
        self._units['Hit logic'] = self.hitlogic
        self.filter = Filter(self.registerfile)
        self._units['Filter'] = self.filter

        self.reset()

    def reset(self):
        for unit in self._units.itervalues():
            unit.reset()

    def __str__(self):
        return '\n\n'.join(frame(name)+'\n'+str(unit)
                           for (name, unit) in self._units.iteritems())

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
        def fmtnumber(n, sz):
            if sz == 1:
                fmt = '{0}'
            else:
                nhex = sz//4 + (1 if sz%4 else 0)
                fmt = '0x{:0'+str(nhex)+'X}'
            return fmt.format(n).rjust(6)
        lines = [frame('Register file')]
        rflines = []
        for name in self.registerfile.dict(nonzero):
            ln = name.ljust(25) + ' '
            sz = self.registerfile.size(name)
            ln += fmtnumber(self.registerfile[name], sz)
            rflines.append(ln)
        lines += sorted(rflines, key=str.lower)
        lines.append('')
        lines.append(frame('Shift register'))
        srlines = []
        for name in self.shiftregister.dict(nonzero):
            ln = name.ljust(25) + ' '
            sz = self.shiftregister.size(name)
            ln += fmtnumber(self.shiftregister[name], sz)
            srlines.append(ln)
        lines += sorted(srlines, key=str.lower)
        print >> f, '\n'.join(lines)


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
    

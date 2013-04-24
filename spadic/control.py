#================================================================
# helper functions
#================================================================
def onoff(value):
    return 'ON' if value else 'OFF'

def frame(title, symbol='=', width=60):
    return '\n'.join(['#' + symbol*(width-1),
                      '# '+title,
                      '#' + symbol*(width-1)])

def checkvalue(v, vmin, vmax, name):
    if v < vmin or v > vmax:
        raise ValueError('valid %s range: %i..%i' %
                         (name, vmin, vmax))


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
        self.set(_LED_USERPIN1, _LED_USERPIN2)

    def set(self, userpin1=None, userpin2=None):
        """Turn the userpin1/2 LEDs on or off."""
        if userpin1 is not None:
            self._userpin1 = 1 if userpin1 else 0
        if userpin2 is not None:
            self._userpin2 = 1 if userpin2 else 0
        value = ((0x10 * self._userpin1) +
                 (0x20 * self._userpin2))
        self._registerfile['overrides'].set(value)

    def __str__(self):
        return ('userpin1: %s  userpin2: %s' %
                (onoff(self._userpin1), onoff(self._userpin2)))
        

#================================================================
# Test data
#================================================================
_TESTDATAIN = 0
_TESTDATAOUT = 0
_TESTDATAGROUP = 0
class TestData:
    """Controls the test data input and output."""
    def __init__(self, registerfile):
        self._registerfile = registerfile
        self.reset()

    def reset(self):
        self.set(_TESTDATAIN, _TESTDATAOUT, _TESTDATAGROUP)

    def set(self, testdatain=None, testdataout=None, group=None):
        """Turn test data input/output on or off and select the group."""
        if testdatain is not None:
            self._testdatain = 1 if testdatain else 0
        if testdataout is not None:
            self._testdataout = 1 if testdataout else 0
        if group is not None:
            self._group = (0 if str(group) in 'aA' else
                          (1 if str(group) in 'bB' else
                          (1 if group else 0)))
        self._registerfile['enableTestInput'].set(self._testdatain)
        self._registerfile['enableTestOutput'].set(self._testdataout)
        self._registerfile['testOutputSelGroup'].set(self._group)

    def __str__(self):
        return ('test data input: %s  test data output: %s  group: %s' %
                (onoff(self._testdatain), onoff(self._testdataout),
                 {0: 'A', 1: 'B'}[self._group]))


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
        self.set(_CMP_TH1, _CMP_TH2, _CMP_DIFFMODE)

    def set(self, threshold1=None, threshold2=None, diffmode=None):
        """Set the two thresholds and turn the diff mode on or off."""
        if threshold1 is not None:
            checkvalue(threshold1, -256, 255, 'threshold1')
            self._threshold1 = threshold1
        if threshold2 is not None:
            checkvalue(threshold2, -256, 255, 'threshold2')
            self._threshold2 = threshold2
        if diffmode is not None:
            self._diffmode = 1 if diffmode else 0
        self._registerfile['threshold1'].set(self._threshold1 % 512)
        self._registerfile['threshold2'].set(self._threshold2 % 512)
        self._registerfile['compDiffMode'].set(self._diffmode)

    def __str__(self):
        return ('threshold 1: %i  threshold 2: %i  diff mode: %s' %
                (self._threshold1, self._threshold2, onoff(self._diffmode)))
        

#================================================================
# Hit logic
#================================================================
_HITLOGIC_MASK = 0xFFFF0000
_HITLOGIC_WINDOW = 16
class HitLogic:
    """Controls the hit logic.
    
    The following settings are controlled globally for all channels:
    - selection mask
    - hit window length
    
    """
    def __init__(self, registerfile):
        self._registerfile = registerfile
        self.reset()

    def reset(self):
        self.set(_HITLOGIC_MASK, _HITLOGIC_WINDOW)

    def set(self, mask=None, window=None):
        """Set the selection mask and the hit window length."""
        if mask is not None:
            if mask < 0 or mask > 0xFFFFFFFF:
                raise ValueError('valid mask range: 0..0xFFFFFFFF')
                # checkvalue() not used here because of hex format
            self._mask = mask
        if window is not None:
            checkvalue(window, 0, 63, 'hit window length')
            self._window = window

        mask_h = self._mask >> 16;
        mask_l = self._mask & 0xFFFF;
        self._registerfile['selectMask_h'].set(mask_h)
        self._registerfile['selectMask_l'].set(mask_l)
        self._registerfile['hitWindowLength'].set(self._window)

    def __str__(self):
        return ('selection mask: 0x%08X  hit window length: %i' %
                (self._mask, self._window))


#================================================================
# Digital channel settings
#================================================================

#----------------------------------------------------------------
# Channel-specific settings
#----------------------------------------------------------------
_DIGCHANNEL_ENABLE = 0
_DIGCHANNEL_ENTRIGGER = 0
class DigitalChannel:
    """Controls the digital channel settings."""
    def __init__(self, registerfile, channel_id):
        self._registerfile = registerfile
        self._id = channel_id
        self.reset()

    def reset(self):
        self.set(_DIGCHANNEL_ENABLE, _DIGCHANNEL_ENTRIGGER)

    def set(self, enable=None, entrigger=None):
        """Turn the channel on/off, enable trigger input."""
        if enable is not None:
            self._enable = 1 if enable else 0
        if entrigger is not None:
            self._entrigger = 1 if entrigger else 0

        i = self._id % 16

        reg_disable = {0: 'disableChannelA',
                       1: 'disableChannelB'}[self._id//16]
        basevalue = self._registerfile[reg_disable].get() & (0xFFFF-(1<<i))
        newvalue = basevalue + (0 if self._enable else (1<<i))
        self._registerfile[reg_disable].set(newvalue)

        reg_trigger = {0: 'triggerMaskA',
                       1: 'triggerMaskB'}[self._id//16]
        basevalue = self._registerfile[reg_trigger].get() & (0xFFFF-(1<<i))
        newvalue = basevalue + ((1<<i) if self._entrigger else 0)
        self._registerfile[reg_trigger].set(newvalue)

    def __str__(self):
        return ('enabled: %s  trigger input: %s' %
                (onoff(self._enable).ljust(3),
                 onoff(self._entrigger).ljust(3)))


#----------------------------------------------------------------
# Neighbor select matrix
#----------------------------------------------------------------
class NeighborMatrix:
    """Controls the neighbor select matrix of one channel group."""
    def __init__(self, registerfile, group):
        self._registerfile = registerfile
        self._group = (0 if str(group) in 'aA' else
                      (1 if str(group) in 'bB' else
                      (1 if group else 0)))
        self._map = {'u0': 0, 'u1': 1, 'u2': 2,
                     'l0': 19, 'l1': 20, 'l2': 21}
        for i in range(16):
            self._map[str(i)] = i+3
        self.reset()

    def reset(self):
        self._targets = ([[0]*3 + [0]*16 + [0]*3 for _ in range(3)] +
                         [[0]*3 + [0]*16 + [0]*3 for _ in range(16)] +
                         [[0]*3 + [0]*16 + [0]*3 for _ in range(3)])
        self.set()

    def set(self, target=None, source=None, enable=None):
        """Turn 'target is triggered by source' on or off."""
        if all(p is not None for p in [target, source, enable]):
            self._set(target, source, enable)
        
        bits = [1 if enable else 0
                for target in self._targets for enable in target]
        for i in range(31):
            name = ('neighborSelectMatrix%s_%i' % 
                    ({0: 'A', 1: 'B'}[self._group], i))
            part = bits[16*i:16*(i+1)]
            value = sum((1<<i)*bit for (i, bit) in enumerate(part))
            self._registerfile[name].set(value)

    def _set(self, target, source, enable):
        tgt_idx = self._map[str(target).lower()]
        src_idx = self._map[str(source).lower()]
        if ((tgt_idx in [0, 1, 2]    and src_idx in [0, 1, 2]   ) or
            (tgt_idx in [19, 20, 21] and src_idx in [19, 20, 21]) or
            (tgt_idx == src_idx)):
            raise ValueError('loops are not allowed!')
        value = 1 if enable else 0
        self._targets[tgt_idx][src_idx] = value

    def __str__(self):
        return '\n'.join(' '.join('x' if enable else '.'
                                  for enable in target)
                         for target in self._targets)


#----------------------------------------------------------------
# All channels
#----------------------------------------------------------------
class Digital:
    """Collection of digital channel controllers.

    Controls the following channel-specific digital settings:
    - channel enable/disable
    - trigger input enable/disable (DLM11)
    - neighbor selection matrix
    
    Individual channels are accessed by 
      <name of Controller instance>.digital.channel[<channel id>]

    Neighbor matrix of groups A/B is accessed by
      <name of Controller instance>.digital.neighbor[<'A' or 'B'>]

    """
    def __init__(self, registerfile):
        self._registerfile = registerfile
        self.channel = [DigitalChannel(self._registerfile, i)
                        for i in range(32)]
        self.neighbor = {'A': NeighborMatrix(self._registerfile, 'A'),
                         'B': NeighborMatrix(self._registerfile, 'B')}
        self.reset()
            
    def reset(self):
        for ch in self.channel:
            ch.reset()
        for nb in self.neighbor.itervalues():
            nb.reset()

    def set(self): # ?
        for ch in self.channel:
            ch.set()

    def __str__(self):
        s = [('channel %2i: ' % ch._id) + str(ch) for ch in self.channel]
        s += ['\nNeighbor matrix (group A)\n'+str(self.neighbor['A'])]
        s += ['\nNeighbor matrix (group B)\n'+str(self.neighbor['B'])]
        return '\n'.join(s)

        
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
        self.set(_FILTER_COEFFA, _FILTER_COEFFB, _FILTER_ENABLE)

    def set(self, coeffa=None, coeffb=None, enable=None, norm=False):
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
        self._registerfile['aCoeffFilter_h'].set(value_a >> 16)
        self._registerfile['aCoeffFilter_l'].set(value_a & 0xFFFF)
        self._registerfile['bCoeffFilter_h'].set(value_b >> 16)
        self._registerfile['bCoeffFilter_l'].set(value_b & 0xFFFF)
        value_enable = sum(en << i for (i, en) in enumerate(self._enable))
        self._registerfile['bypassFilterStage'].set((~value_enable) % 32)

    def __str__(self):
        p = self._position
        return ('coeff. a: %4i  coeff. b: %4i  enabled: %s' %
                (self._coeffa[p], self._coeffb[p], onoff(self._enable[p])))

#----------------------------------------------------------------
# Single stage (half)
#----------------------------------------------------------------
class StageZero(Stage):
    """Controls a half stage which has no 'a' coefficient."""

    def set(self, coeffb=None, enable=None, norm=False):
        """Set the 'b' coefficient and turn the stage on or off."""
        Stage.set(self, None, coeffb, enable, norm)

    def __str__(self):
        p = self._position
        return ('                coeff. b: %4i  enabled: %s' %
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
        self.set(_FILTER_SCALING, _FILTER_OFFSET, _FILTER_ENABLE)

    def set(self, scaling=None, offset=None, enable=None, norm=False):
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

        self._registerfile['offsetFilter'].set(self._offset % 512)
        self._registerfile['scalingFilter'].set(self._scaling % 512)
        value_enable = sum(en << i for (i, en) in enumerate(self._enable))
        self._registerfile['bypassFilterStage'].set((~value_enable) % 32)

    def __str__(self):
        p = self._position
        return ('scaling: %5i  offset: %6i  enabled: %s' %
                (self._scaling, self._offset, onoff(self._enable[p])))

#----------------------------------------------------------------
# Whole filter
#----------------------------------------------------------------
class Filter:
    """Controls the digital filter settings.
    
    Individual filter stages are accessed by
      <name of controller instance>.filter.stage[<index>]
      
    Index    Type             Settings
    ---------------------------------------------------
      0      half stage       coefficient b, enable
     1-3     full stage       coefficients a, b, enable
      4      scaling/offset   scaling, offset, enable

    """
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

    def set(self): # ?
        for s in self.stage:
            s.set()

    def __str__(self):
        return '\n'.join(('Stage %i: ' % i) + str(s)
                         for (i, s) in enumerate(self.stage))


#================================================================
# Analog frontend
#================================================================

#----------------------------------------------------------------
# Channel-specific settings
#----------------------------------------------------------------
_FECHANNEL_BASELINE = 0
_FECHANNEL_ENCSA = 0
_FECHANNEL_ENADC = 0
class FrontendChannel:
    """Analog frontend channel specific controller."""

    def __init__(self, registerchain, channel_id):
        self._registerchain = registerchain
        self._id = channel_id
        self.reset()

    def reset(self):
        self._frontend = _FRONTEND_SELECT
        self.set(_FECHANNEL_BASELINE, _FECHANNEL_ENCSA, _FECHANNEL_ENADC)

    def set(self, baseline=None, enablecsa=None, enableadc=None):
        """Trim the baseline, turn the CSA on/off, turn the ADC on/off."""
        if baseline is not None:
            if baseline < 0 or baseline > 127:
                raise ValueError('valid baseline range: 0..127')
            self._baseline = baseline
        if enablecsa is not None:
            self._enablecsa = 1 if enablecsa else 0
        if enableadc is not None:
            self._enableadc = 1 if enableadc else 0

        directmode = self._registerchain._directmode
        self._registerchain._directmode = False

        i = str(self._id)
        self._registerchain['baselineTrimP_'+i].set(self._baseline)
        self._registerchain['frontEndSelNP_'+i].set(self._frontend)
        self._registerchain['enSignalAdc_'+i].set(self._enableadc)
        self._registerchain['enAmpN_'+i].set(1 if (self._enablecsa and
                                                   self._frontend == 0)
                                               else 0)
        self._registerchain['enAmpP_'+i].set(1 if (self._enablecsa and
                                                   self._frontend == 1)
                                               else 0)
        if directmode:
            self._registerchain.apply()
        self._registerchain._directmode = directmode

    def _select_frontend(self, frontend):
        self._frontend = frontend
        self.set()

    def __str__(self):
        return ('baseline trim: %3i  CSA enabled: %s  ADC connected: %s' %
                (self._baseline, onoff(self._enablecsa).ljust(3),
                                 onoff(self._enableadc).ljust(3)))

#----------------------------------------------------------------
# Global settings
#----------------------------------------------------------------
_FRONTEND_SELECT = 1 # N=0, P=1
_FRONTEND_BASELINE = 0
_FRONTEND_PCASC = 0
_FRONTEND_NCASC = 0
_FRONTEND_PSOURCEBIAS = 0
_FRONTEND_NSOURCEBIAS = 0
_FRONTEND_XFB = 0
class Frontend:
    """SPADIC 1.0 analog frontend controller.

    Controls the following global settings of the analog frontend:
    - frontend N or P
    - baseline trim
    - CSA bias settings (pCasc, nCasc, pSourceBias, nSourceBias, xFB)
    
    Additionally controls the following channel-specific settings:
    - baseline trim
    - CSA enable/disable
    - ADC enable/disable

    Individual channels are accessed by 
      <name of Controller instance>.frontend.channel[<channel id>]

    For example, after
      c = Controller(...)
    the channel-specific settings of the analog frontend in channel number 3
    are accessed by
      c.frontend.channel[3]

    """
    def __init__(self, registerchain):
        self._registerchain = registerchain
        self.channel = [FrontendChannel(self._registerchain, i)
                        for i in range(32)]
        self.reset()

    def reset(self):
        for ch in self.channel:
            ch.reset()
        self.set(_FRONTEND_SELECT, _FRONTEND_BASELINE,
                 _FRONTEND_PCASC, _FRONTEND_NCASC,
                 _FRONTEND_PSOURCEBIAS, _FRONTEND_NSOURCEBIAS,
                 _FRONTEND_XFB)

    def set(self, frontend=None, baseline=None, pcasc=None, ncasc=None,
                  psourcebias=None, nsourcebias=None, xfb=None):
        """Select N/P frontend, set global baseline trim, set CSA bias."""

        if frontend is not None:
            self._frontend = (0 if str(frontend) in 'nN' else
                             (1 if str(frontend) in 'pP' else
                             (1 if frontend else 0)))
            for ch in self.channel:
                ch._select_frontend(self._frontend)

        if baseline is not None:
            checkvalue(baseline, 0, 127, 'baseline')
            self._baseline = baseline
        if pcasc is not None:
            checkvalue(pcasc, 0, 127, 'pcasc')
            self._pcasc = pcasc
        if ncasc is not None:
            checkvalue(ncasc, 0, 127, 'ncasc')
            self._ncasc = ncasc
        if psourcebias is not None:
            checkvalue(psourcebias, 0, 127, 'psourcebias')
            self._psourcebias = psourcebias
        if nsourcebias is not None:
            checkvalue(nsourcebias, 0, 127, 'nsourcebias')
            self._nsourcebias = nsourcebias
        if xfb is not None:
            checkvalue(xfb, 0, 127, 'xfb')
            self._xfb = xfb

        directmode = self._registerchain._directmode
        self._registerchain._directmode = False

        self._registerchain['baselineTrimN'].set(self._baseline)
        self._registerchain['DecSelectNP'].set(self._frontend)

        r = {0: ['pCascN','nCascN','pSourceBiasN','nSourceBiasN','pFBN'],
             1: ['pCascP','nCascP','pSourceBiasP','nSourceBiasP','nFBP']}
        v = [self._pcasc, self._ncasc,
                        self._psourcebias, self._nsourcebias, self._xfb]

        for name in r[1-self._frontend]:
            self._registerchain[name].set(0)
        for (name, value) in zip(r[self._frontend], v):
            self._registerchain[name].set(value)

        if directmode:
            self._registerchain.apply()
        self._registerchain._directmode = directmode

    def __str__(self):
        s = [('frontend: %s  baseline: %3i  pCasc: %3i  nCasc: %3i\n'
              'pSourceBias: %3i  nSourceBias: %3i  xFB: %3i\n' %
              ({0: 'N', 1: 'P'}[self._frontend], self._baseline,
              self._pcasc, self._ncasc, self._psourcebias,
              self._nsourcebias, self._xfb))]
        s += [('channel %2i: ' % ch._id) + str(ch) for ch in self.channel]
        return '\n'.join(s)


#================================================================
# ADC bias
#================================================================
_ADC_VNDEL = 0
_ADC_VPDEL = 0
_ADC_VPLOADFB = 0
_ADC_VPLOADFB2 = 0
_ADC_VPFB = 0
_ADC_VPAMP = 0
class AdcBias:
    """Controls the ADC bias settings."""
    def __init__(self, registerchain):
        self._registerchain = registerchain
        self.reset()

    def reset(self):
        self.set(_ADC_VNDEL, _ADC_VPDEL, _ADC_VPLOADFB, _ADC_VPLOADFB2,
                 _ADC_VPFB, _ADC_VPAMP)

    def set(self, vndel=None, vpdel=None, vploadfb=None,
                  vploadfb2=None, vpfb=None, vpamp=None):
        """Set VNDel, VPDel, VPLoadFB, VPLoadFB2, VPFB, VPAmp values."""
        if vndel is not None:
            checkvalue(vndel, 0, 127, 'VNDel')
            self._vndel = vndel
        if vpdel is not None:
            checkvalue(vpdel, 0, 127, 'VPDel')
            self._vpdel = vpdel
        if vploadfb is not None:
            checkvalue(vploadfb, 0, 127, 'VPLoadFB')
            self._vploadfb = vploadfb
        if vploadfb2 is not None:
            checkvalue(vploadfb2, 0, 127, 'VPLoadFB2')
            self._vploadfb2 = vploadfb2
        if vpfb is not None:
            checkvalue(vpfb, 0, 127, 'VPFB')
            self._vpfb = vpfb
        if vpamp is not None:
            checkvalue(vpamp, 0, 127, 'VPAmp')
            self._vpamp = vpamp

        directmode = self._registerchain._directmode
        self._registerchain._directmode = False

        self._registerchain['VNDel'].set(self._vndel)
        self._registerchain['VPDel'].set(self._vpdel)
        self._registerchain['VPLoadFB'].set(self._vploadfb)
        self._registerchain['VPLoadFB2'].set(self._vploadfb2)
        self._registerchain['VPFB'].set(self._vpfb)
        self._registerchain['VPAmp'].set(self._vpamp)

        if directmode:
            self._registerchain.apply()
        self._registerchain._directmode = directmode

    def __str__(self):
        return ('VNDel: %3i  VPDel: %3i  VPLoadFB: %3i\n'
                'VPLoadFB2: %3i  VPFB: %3i  VPAmp: %3i' %
                (self._vndel, self._vpdel, self._vploadfb,
                 self._vploadfb2, self._vpfb, self._vpamp))


#================================================================
# Monitor
#================================================================
_MON_SOURCE = 1 # ADC=0, CSA=1
_MON_CHANNEL = 0
_MON_ENABLE = 0
class Monitor:
    """Monitor controller.
    
    Controls the following settings of the monitor bus:
    - enable/disable
    - source selection: ADC or CSA
    - channel selection

    """
    def __init__(self, registerchain):
        self._registerchain = registerchain
        self.reset()

    def reset(self):
        self.set(_MON_SOURCE, _MON_CHANNEL, _MON_ENABLE)
        
    def set(self, source=None, channel=None, enable=None):
        """Select the monitor source, channel, and turn it on or off."""
        if source is not None:
            self._source = (1 if str(source).lower() == 'csa' else
                           (0 if str(source).lower() == 'adc' else
                           (1 if source else 0)))
        if channel is not None:
            if not channel in range(32):
                raise ValueError('valid channel range: 0..31')
            self._channel = channel
        if enable is not None:
            self._enable = 1 if enable else 0

        directmode = self._registerchain._directmode
        self._registerchain._directmode = False

        self._registerchain['SelMonitor'].set(self._source)
        enMonitorAdc = [0]*32
        ampToBus = [0]*32
        if self._enable:
            {0: enMonitorAdc, 1: ampToBus}[self._source][self._channel] = 1
        for ch in range(32):
            self._registerchain['enMonitorAdc_'+str(ch)].set(enMonitorAdc[ch])
            self._registerchain['ampToBus_'+str(ch)].set(ampToBus[ch])

        if directmode:
            self._registerchain.apply()
        self._registerchain._directmode = directmode

    def __str__(self):
        return ('monitor source: %s  channel: %2i  enabled: %s' %
                ({0: 'ADC', 1: 'CSA'}[self._source], self._channel,
                 onoff(self._enable)))


#================================================================
# Main control
#================================================================
class Controller:
    """SPADIC 1.0 configuration controller.
    
    Contains the following control units:

    adcbias
    comparator
    digital
    filter
    frontend
    hitlogic
    led
    monitor
    testdata
    
    To get help on one of the units, type
      help(<name of controller variable>.<name of unit>)

    For example, if a Controller instance was created by
      c = Controller(...)
    and documentation about the hit logic settings is needed, type
      help(c.hitlogic)

    """
    def __init__(self, spadic):
        self._spadic = spadic
        self._directmode = False
        self.registerfile = spadic._registerfile
        self.registerchain = spadic._registerchain

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
        self.monitor = Monitor(self.registerchain)
        self._units['Monitor'] = self.monitor
        self.frontend = Frontend(self.registerchain)
        self._units['Frontend'] = self.frontend
        self.adcbias = AdcBias(self.registerchain)
        self._units['ADC bias'] = self.adcbias
        self.digital = Digital(self.registerfile)
        self._units['Digital'] = self.digital

        self.reset()
        self.apply()

    def reset(self):
        """Reset all control units."""
        for unit in self._units.itervalues():
            unit.reset()

    def apply(self):
        """Update register values from control units and write RF/SR."""
        for unit in self._units.itervalues():
            unit.set()
        self.registerfile.apply()
        self.registerchain.apply()

    def set_directmode(self, mode):
        """Set direct mode of register file and shift register."""
        self._directmode = mode
        self.registerfile.set_directmode(mode)
        self.registerchain.set_directmode(mode)

    def __str__(self):
        return '\n\n'.join(frame(name)+'\n'+str(unit)
                           for (name, unit) in self._units.iteritems())

    #def _write_registerchain(self, config=None):
    #    """Perform the shift register write operation."""
    #    if config is not None:
    #        self.registerchain.load(config)
    #    self.led(1)
    #    self.registerchain.write()
    #    self.led(0)

    #def _write_registerfile(self, config):
    #    """Write a configuration into the register file."""
    #    self.led(1)
    #    self.registerfile.load(config)
    #    self.led(0)

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
        for name in self.registerchain.dict(nonzero):
            ln = name.ljust(25) + ' '
            sz = self.registerchain.size(name)
            ln += fmtnumber(self.registerchain[name], sz)
            srlines.append(ln)
        lines += sorted(srlines, key=str.lower)
        print >> f, '\n'.join(lines)

    def load(self, f):
        """Load the configuration from a text file.
        
        (not yet implemented)"""
        raise NotImplementedError


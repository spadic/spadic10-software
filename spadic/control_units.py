from control_base import *

#================================================================
# Digital channel settings
#================================================================

#----------------------------------------------------------------
# Channel-specific settings
#----------------------------------------------------------------
_DIGCHANNEL_ENABLE = 0
_DIGCHANNEL_ENTRIGGER = 0
class DigitalChannel(ControlUnitBase):
    """Controls the digital channel settings."""
    def __init__(self, registerfile, channel_id):
        self._registerfile = registerfile
        self._id = channel_id
        self.update()

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

    def apply(self):
        self._registerfile['disableChannelA'].apply()
        self._registerfile['disableChannelB'].apply()
        self._registerfile['triggerMaskA'].apply()
        self._registerfile['triggerMaskB'].apply()

    def update(self):
        i = self._id % 16

        reg_disable = {0: 'disableChannelA',
                       1: 'disableChannelB'}[self._id//16]
        dis = self._registerfile[reg_disable].read()
        self._enable = (~dis >> i) & 1

        reg_trigger = {0: 'triggerMaskA',
                       1: 'triggerMaskB'}[self._id//16]
        trig = self._registerfile[reg_trigger].read()
        self._entrigger = (trig >> i) & 1

    def get(self):
        return {'enable': self._enable,
                'entrigger': self._entrigger}

    def __str__(self):
        return ('enabled: %s  trigger input: %s' %
                (onoff(self._enable).ljust(3),
                 onoff(self._entrigger).ljust(3)))


#----------------------------------------------------------------
# Neighbor select matrix
#----------------------------------------------------------------
NB_MAP = {'U0':  0, 'U1':  1, 'U2':  2,
          'L0': 19, 'L1': 20, 'L2': 21}
for i in range(16):
    NB_MAP[str(i)] = i+3

NB_MAP_INV = { 0: 'U0',  1: 'U1',  2: 'U2',
              19: 'L0', 20: 'L1', 21: 'L2'}
for i in range(16):
    NB_MAP_INV[i+3] = i

class NeighborMatrix(ControlUnitBase):
    """Controls the neighbor select matrix of one channel group."""
    def __init__(self, registerfile, group):
        self._registerfile = registerfile
        self._group = (0 if str(group) in 'aA' else
                      (1 if str(group) in 'bB' else
                      (1 if group else 0)))
        self.reset()
        self.update()

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
        tgt_idx = NB_MAP[str(target).upper()]
        src_idx = NB_MAP[str(source).upper()]
        if ((tgt_idx in [ 0,  1,  2] and src_idx in [ 0,  1,  2]) or
            (tgt_idx in [19, 20, 21] and src_idx in [19, 20, 21]) or
            (tgt_idx == src_idx)):
            raise ValueError('invalid source/target combination!')
        value = 1 if enable else 0
        self._targets[tgt_idx][src_idx] = value

    def apply(self):
        for i in range(31):
            name = ('neighborSelectMatrix%s_%i' % 
                    ({0: 'A', 1: 'B'}[self._group], i))
            self._registerfile[name].apply()

    def update(self):
        bits = []
        for i in range(31):
            name = ('neighborSelectMatrix%s_%i' % 
                    ({0: 'A', 1: 'B'}[self._group], i))
            x = self._registerfile[name].read()
            bits += [(x >> i) & 1 for i in range(16)]
        for tgt in range(22):
            for src in range(22):
                self._targets[tgt][src] = bits[22*tgt+src]

    def get(self):
        result = {}
        for (tgt_idx, src_list) in enumerate(self._targets):
            src = [NB_MAP_INV[src_idx]
                   for (src_idx, en) in enumerate(src_list) if en]
            if src:
                result[NB_MAP_INV[tgt_idx]] = src
        return result

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
        self.update()
            
    def reset(self):
        for ch in self.channel:
            ch.reset()
        for nb in self.neighbor.itervalues():
            nb.reset()

    def apply(self):
        for ch in self.channel:
            ch.apply()

    def update(self):
        for ch in self.channel:
            ch.update()

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
class Stage(ControlUnitBase):
    """Controls a filter stage."""
    def __init__(self, registerfile, coeffa_list, coeffb_list,
                                                  enable_list, position):
        self._registerfile = registerfile
        self._coeffa = coeffa_list
        self._coeffb = coeffb_list
        self._enable = enable_list
        self._position = position
        self.reset()
        self.update()

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

    def apply(self):
        self._registerfile['aCoeffFilter_h'].apply()
        self._registerfile['aCoeffFilter_l'].apply()
        self._registerfile['bCoeffFilter_h'].apply()
        self._registerfile['bCoeffFilter_l'].apply()
        self._registerfile['bypassFilterStage'].apply()

    def update(self):
        p = self._position
        ra_h = self._registerfile['aCoeffFilter_h'].read() 
        ra_l = self._registerfile['aCoeffFilter_l'].read()
        rb_h = self._registerfile['bCoeffFilter_h'].read()
        rb_l = self._registerfile['bCoeffFilter_l'].read()
        ra = (ra_h << 16) + ra_l
        rb = (rb_h << 16) + rb_l
        a = (ra >> (6*(p-1))) & 0x3F if p > 0 else 0
        b = (rb >> (6*p))     & 0x3F
        self._coeffa[p] = (a if a < 32 else a-64)
        self._coeffb[p] = (b if b < 32 else b-64)
        byp = self._registerfile['bypassFilterStage'].read()
        self._enable[p] = (~byp >> p) & 1

    def get(self):
        p = self._position
        return {'coeffa': self._coeffa[p],
                'coeffb': self._coeffb[p],
                'enable': self._enable[p]}

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

    def get(self):
        result = Stage.get(self)
        del result['coeffa']
        return result

    def __str__(self):
        p = self._position
        return ('                coeff. b: %4i  enabled: %s' %
                (self._coeffb[p], onoff(self._enable[p])))

#----------------------------------------------------------------
# Scaling/offset
#----------------------------------------------------------------
class ScalingOffset(ControlUnitBase):
    """Controls a scaling/offset stage."""
    def __init__(self, registerfile, enable_list, position):
        self._registerfile = registerfile
        self._enable = enable_list
        self._position = position
        self.reset()
        self.update()

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

    def apply(self):
        self._registerfile['offsetFilter'].apply()
        self._registerfile['scalingFilter'].apply()
        self._registerfile['bypassFilterStage'].apply()

    def update(self):
        scaling = self._registerfile['scalingFilter'].read()
        offset = self._registerfile['offsetFilter'].read()
        byp = self._registerfile['bypassFilterStage'].read()
        self._scaling = scaling if scaling < 256 else scaling-512
        self._offset = offset if offset < 256 else offset-512
        self._enable[self._position] = (~byp >> self._position) & 1
    
    def get(self):
        return {'scaling': self._scaling,
                'offset': self._offset,
                'enable': self._enable[self._position]}

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
        self.update()

    def reset(self):
        for s in self.stage:
            s.reset()

    def apply(self):
        for s in self.stage:
            s.apply()

    def update(self):
        for s in self.stage:
            s.update()

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

    def __init__(self, shiftregister, channel_id):
        self._shiftregister = shiftregister
        self._id = channel_id
        self.reset()

    def _select_frontend(self, frontend):
        self._frontend = frontend
        self.set()

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

        i = str(self._id)
        self._shiftregister['baselineTrimP_'+i].set(self._baseline)
        self._shiftregister['frontEndSelNP_'+i].set(self._frontend)
        self._shiftregister['enSignalAdc_'+i].set(self._enableadc)
        self._shiftregister['enAmpN_'+i].set(1 if (self._enablecsa and
                                                   self._frontend == 0)
                                               else 0)
        self._shiftregister['enAmpP_'+i].set(1 if (self._enablecsa and
                                                   self._frontend == 1)
                                               else 0)

    def apply(self):
        self._shiftregister.apply()
        
    def write(self, *args, **kwargs):
        self.set(*args, **kwargs)
        self.apply()

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
    def __init__(self, shiftregister):
        self._shiftregister = shiftregister
        self.channel = [FrontendChannel(self._shiftregister, i)
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

        self._shiftregister['baselineTrimN'].set(self._baseline)
        self._shiftregister['DecSelectNP'].set(self._frontend)

        r = {0: ['pCascN','nCascN','pSourceBiasN','nSourceBiasN','pFBN'],
             1: ['pCascP','nCascP','pSourceBiasP','nSourceBiasP','nFBP']}
        v = [self._pcasc, self._ncasc,
                        self._psourcebias, self._nsourcebias, self._xfb]

        for name in r[1-self._frontend]:
            self._shiftregister[name].set(0)
        for (name, value) in zip(r[self._frontend], v):
            self._shiftregister[name].set(value)

    def apply(self):
        self._shiftregister.apply()

    def write(self, *args, **kwargs):
        self.set(*args, **kwargs)
        self.apply()

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
    def __init__(self, shiftregister):
        self._shiftregister = shiftregister
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

        self._shiftregister['VNDel'].set(self._vndel)
        self._shiftregister['VPDel'].set(self._vpdel)
        self._shiftregister['VPLoadFB'].set(self._vploadfb)
        self._shiftregister['VPLoadFB2'].set(self._vploadfb2)
        self._shiftregister['VPFB'].set(self._vpfb)
        self._shiftregister['VPAmp'].set(self._vpamp)

    def apply(self):
        self._shiftregister.apply()

    def write(self, *args, **kwargs):
        self.set(*args, **kwargs)
        self.apply()

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
    def __init__(self, shiftregister):
        self._shiftregister = shiftregister
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

        self._shiftregister['SelMonitor'].set(self._source)
        enMonitorAdc = [0]*32
        ampToBus = [0]*32
        if self._enable:
            {0: enMonitorAdc, 1: ampToBus}[self._source][self._channel] = 1
        for ch in range(32):
            self._shiftregister['enMonitorAdc_'+str(ch)].set(enMonitorAdc[ch])
            self._shiftregister['ampToBus_'+str(ch)].set(ampToBus[ch])

    def apply(self):
        self._shiftregister.apply()

    def write(self, *args, **kwargs):
        self.set(*args, **kwargs)
        self.apply()

    def __str__(self):
        return ('monitor source: %s  channel: %2i  enabled: %s' %
                ({0: 'ADC', 1: 'CSA'}[self._source], self._channel,
                 onoff(self._enable)))


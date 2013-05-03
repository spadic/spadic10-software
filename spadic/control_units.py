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
        self.reset()
            
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


from control_base import *

_HITLOGIC_MASK = 0xFFFF0000
_HITLOGIC_WINDOW = 16
_HITLOGIC_TH1 = 0
_HITLOGIC_TH2 = 0
_HITLOGIC_DIFFMODE = 0
class HitLogic(ControlUnitBase):
    """Controls the hit logic.
    
    The following settings are controlled globally for all channels:
    - selection mask
    - hit window length
    - dual threshold
    - differential trigger mode
    """
    def __init__(self, registerfile):
        self._registerfile = registerfile
        self.update()

    def reset(self):
        self.set(_HITLOGIC_MASK, _HITLOGIC_WINDOW,
                 _HITLOGIC_TH1, _HITLOGIC_TH2, _HITLOGIC_DIFFMODE)

    def set(self, mask=None, window=None,
                  threshold1=None, threshold2=None, diffmode=None):
        if mask is not None:
            if mask < 0 or mask > 0xFFFFFFFF:
                raise ValueError('valid mask range: 0..0xFFFFFFFF')
                # checkvalue() not used here because of hex format
            self._mask = mask

        if window is not None:
            checkvalue(window, 0, 63, 'hit window length')
            self._window = window

        if threshold1 is not None:
            checkvalue(threshold1, -256, 255, 'threshold1')
            self._threshold1 = threshold1

        if threshold2 is not None:
            checkvalue(threshold2, -256, 255, 'threshold2')
            self._threshold2 = threshold2

        if diffmode is not None:
            self._diffmode = 1 if diffmode else 0

        mask_h = self._mask >> 16;
        mask_l = self._mask & 0xFFFF;
        self._registerfile['selectMask_h'].set(mask_h)
        self._registerfile['selectMask_l'].set(mask_l)
        self._registerfile['hitWindowLength'].set(self._window)
        self._registerfile['threshold1'].set(self._threshold1 % 512)
        self._registerfile['threshold2'].set(self._threshold2 % 512)
        self._registerfile['compDiffMode'].set(self._diffmode)

    def apply(self):
        self._registerfile['selectMask_h'].apply()
        self._registerfile['selectMask_l'].apply()
        self._registerfile['hitWindowLength'].apply()
        self._registerfile['threshold1'].apply()
        self._registerfile['threshold2'].apply()
        self._registerfile['compDiffMode'].apply()

    def update(self):
        mask_h = self._registerfile['selectMask_h'].read()
        mask_l = self._registerfile['selectMask_l'].read()
        self._mask = (mask_h << 16) + mask_l

        self._window = self._registerfile['hitWindowLength'].read()

        th1 = self._registerfile['threshold1'].read()
        th2 = self._registerfile['threshold2'].read()
        self._threshold1 = th1 if th1 < 256 else th1-512
        self._threshold2 = th2 if th2 < 256 else th2-512

        self._diffmode = self._registerfile['compDiffMode'].read()

    def get(self):
        return {'mask': self._mask,
                'window': self._window,
                'threshold1': self._threshold1,
                'threshold2': self._threshold2,
                'diffmode': self._diffmode}

    def __str__(self):
        s = ['selection mask: 0x%08X  hit window length: %i' %
             (self._mask, self._window),
             'threshold 1: %i  threshold 2: %i  diff mode: %s' %
             (self._threshold1, self._threshold2, onoff(self._diffmode))]
        return '\n'.join(s)


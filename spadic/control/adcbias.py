from .base import *

_ADC_VNDEL = 0
_ADC_VPDEL = 0
_ADC_VPLOADFB = 0
_ADC_VPLOADFB2 = 0
_ADC_VPFB = 0
_ADC_VPAMP = 0
_ADC_BASELINE = 0

class AdcBias(ControlUnitBase):
    """Controls the ADC bias settings."""
    def __init__(self, shiftregister):
        self._shiftregister = shiftregister
        self.reset()

    def reset(self):
        self.set(_ADC_VNDEL, _ADC_VPDEL, _ADC_VPLOADFB, _ADC_VPLOADFB2,
                 _ADC_VPFB, _ADC_VPAMP, _ADC_BASELINE)

    def set(self, vndel=None, vpdel=None, vploadfb=None,
                  vploadfb2=None, vpfb=None, vpamp=None, baseline=None):
        """
        Set VNDel, VPDel, VPLoadFB, VPLoadFB2, VPFB, VPAmp, and
        baselineTrimN values.
        """
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
        if baseline is not None:
            checkvalue(baseline, 0, 127, 'baseline')
            self._baseline = baseline

        self._shiftregister['VNDel'].set(self._vndel)
        self._shiftregister['VPDel'].set(self._vpdel)
        self._shiftregister['VPLoadFB'].set(self._vploadfb)
        self._shiftregister['VPLoadFB2'].set(self._vploadfb2)
        self._shiftregister['VPFB'].set(self._vpfb)
        self._shiftregister['VPAmp'].set(self._vpamp)
        self._shiftregister['baselineTrimN'].set(self._baseline)

    def apply(self):
        self._shiftregister['VNDel'].apply()
        self._shiftregister['VPDel'].apply()
        self._shiftregister['VPLoadFB'].apply()
        self._shiftregister['VPLoadFB2'].apply()
        self._shiftregister['VPFB'].apply()
        self._shiftregister['VPAmp'].apply()
        self._shiftregister['baselineTrimN'].apply()

    def update(self):
        self._vndel = self._shiftregister['VNDel'].read()
        self._vpdel = self._shiftregister['VPDel'].read()
        self._vploadfb = self._shiftregister['VPLoadFB'].read()
        self._vploadfb2 = self._shiftregister['VPLoadFB2'].read()
        self._vpfb = self._shiftregister['VPFB'].read()
        self._vpamp = self._shiftregister['VPAmp'].read()
        self._baseline = self._shiftregister['baselineTrimN'].read()

    def get(self):
        return {'vndel': self._vndel,
                'vpdel': self._vpdel,
                'vploadfb': self._vploadfb,
                'vploadfb2': self._vploadfb2,
                'vpfb': self._vpfb,
                'vpamp': self._vpamp,
                'baseline': self._baseline}

    def __str__(self):
        return ('VNDel: %3i  VPDel: %3i  VPLoadFB: %3i\n'
                'VPLoadFB2: %3i  VPFB: %3i  VPAmp: %3i\n'
                'baseline: %3i' %
                (self._vndel, self._vpdel, self._vploadfb,
                 self._vploadfb2, self._vpfb, self._vpamp, self._baseline))


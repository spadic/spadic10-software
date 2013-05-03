from control_base import *

#----------------------------------------------------------------
# Channel-specific settings
#----------------------------------------------------------------
_FECHANNEL_BASELINE = 0
_FECHANNEL_ENCSA = 0
_FECHANNEL_ENADC = 0
class FrontendChannel(ControlUnitBase):
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

    def update(self):
        self._shiftregister.update()
        i = str(self._id)
        self._baseline = self._shiftregister['baselineTrimP_'+i].get()
        self._frontend = self._shiftregister['frontEndSelNP_'+i].get()
        self._enableadc = self._shiftregister['enSignalAdc_'+i].get()
        enamp = {0: 'enAmpN_', 1: 'enAmpP_'}[self._frontend]
        self._enablecsa = self._shiftregister[enamp+i].get()

    def get(self):
        return {'baseline': self._baseline,
                'enablecsa': self._enablecsa,
                'enableadc': self._enableadc}

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

class Frontend(ControlUnitBase):
    """SPADIC 1.0 analog frontend controller.

    Controls the following global settings of the analog frontend:
    - frontend N or P
    - baseline trim
    - CSA bias settings (pCasc, nCasc, pSourceBias, nSourceBias, xFB)
    
    Additionally controls the following channel-specific settings:
    - baseline trim
    - CSA enable/disable
    - ADC enable/disable
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

    def update(self):
        self._shiftregister.update()

        self._baseline = self._shiftregister['baselineTrimN'].get()
        self._frontend = self._shiftregister['DecSelectNP'].get()
        fe ={0: 'N', 1: 'P'}[self._frontend] 
        self._pcasc = self._shiftregister['pCasc'+fe].get()
        self._ncasc = self._shiftregister['nCasc'+fe].get()
        self._psourcebias = self._shiftregister['pSourceBias'+fe].get()
        self._nsourcebias = self._shiftregister['nSourceBias'+fe].get()
        xfb = {0: 'pFBN', 1: 'nFBP'}[self._frontend]
        self._xfb = self._shiftregister[xfb].get()

        for ch in self.channel:
            ch.update()

    def get(self):
        return {'frontend': {0: 'N', 1: 'P'}[self._frontend],
                'pcasc': self._pcasc, 'ncasc': self._ncasc,
                'psourcebias': self._psourcebias,
                'nsourcebias': self._nsourcebias,
                'xfb': self._xfb}

    def __str__(self):
        s = [('frontend: %s  baseline: %3i  pCasc: %3i  nCasc: %3i\n'
              'pSourceBias: %3i  nSourceBias: %3i  xFB: %3i\n' %
              ({0: 'N', 1: 'P'}[self._frontend], self._baseline,
              self._pcasc, self._ncasc, self._psourcebias,
              self._nsourcebias, self._xfb))]
        s += [('channel %2i: ' % ch._id) + str(ch) for ch in self.channel]
        return '\n'.join(s)


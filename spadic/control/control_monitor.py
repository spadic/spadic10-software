from control_base import *

_MON_SOURCE = 1 # ADC=0, CSA=1
_MON_CHANNEL = 0
_MON_ENABLE = 0

class Monitor(ControlUnitBase):
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

    def update(self):
        self._shiftregister.update()
        self._source = self._shiftregister['SelMonitor'].get()
        reg = {0: 'enMonitorAdc_', 1: 'ampToBus_'}[self._source]
        for ch in range(32):
            en = self._shiftregister[reg+str(ch)].get()
            if en:
                self._channel = ch
                break
        self._enable = en

    def get(self):
        return {'source': {0: 'ADC', 1: 'CSA'}[self._source],
                'channel': self._channel,
                'enable': self._enable}

    def __str__(self):
        return ('monitor source: %s  channel: %2i  enabled: %s' %
                ({0: 'ADC', 1: 'CSA'}[self._source], self._channel,
                 onoff(self._enable)))


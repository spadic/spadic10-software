from control_base import *

_LED_USERPIN1 = 0
_LED_USERPIN2 = 0
class Led(ControlUnitBase):
    """Controls the userpin1/2 LEDs."""
    def __init__(self, registerfile):
        self._registerfile = registerfile
        self.update()

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

    def apply(self):
        self._registerfile['overrides'].apply()

    def update(self):
        value = self._registerfile['overrides'].read()
        self._userpin1 = (value & 0x10) >> 4
        self._userpin2 = (value & 0x20) >> 5

    def get(self):
        return {'userpin1': self._userpin1,
                'userpin2': self._userpin2}

    def __str__(self):
        return ('userpin1: %s  userpin2: %s' %
                (onoff(self._userpin1), onoff(self._userpin2)))
        

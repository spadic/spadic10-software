from .base import *

_FILTER_COEFFA = 0
_FILTER_COEFFB = 0
_FILTER_ENABLE = 0
_FILTER_SCALING = 32
_FILTER_OFFSET = 0

#   """Controls the digital filter settings.
#   
#   Individual filter stages are accessed by
#     <name of controller instance>.filter.stage[<index>]
#     
#   Index    Type             Settings
#   ---------------------------------------------------
#     0      half stage       coefficient b, enable
#    1-3     full stage       coefficients a, b, enable
#     4      scaling/offset   scaling, offset, enable
#
#   """

class Filter(ControlUnitBase):
    """Controls the digital filter."""
    def __init__(self, registerfile):
        self._registerfile = registerfile
        self._coeffa = dict((i, _FILTER_COEFFA) for i in range(1, 4))
        self._coeffb = dict((i, _FILTER_COEFFB) for i in range(4))
        self._enable = dict((i, _FILTER_ENABLE) for i in range(5))
        self.reset()

    def reset(self):
        self.set(coeffa = [_FILTER_COEFFA]*4,
                 coeffb = [_FILTER_COEFFB]*4,
                 enable = [_FILTER_ENABLE]*5,
                 scaling = _FILTER_SCALING,
                 offset  = _FILTER_OFFSET)

    def set(self, coeffa=None, coeffb=None, enable=None,
                  scaling=None, offset=None):
        if coeffa is not None:
            if isinstance(coeffa, list) and len(coeffa) != 4:
                raise ValueError('coefficient list must contain 4 values')
            for i in self._coeffa:
                try:
                    c = coeffa[i]
                    checkvalue(c, -32, 31, 'coefficient')
                    self._coeffa[i] = c
                except KeyError:
                    pass

        if coeffb is not None:
            if isinstance(coeffb, list) and len(coeffb) != 4:
                raise ValueError('coefficient list must contain 4 values')
            for i in self._coeffb:
                try:
                    c = coeffb[i]
                    checkvalue(c, -32, 31, 'coefficient')
                    self._coeffb[i] = c
                except KeyError:
                    pass

        if enable is not None:
            if isinstance(enable, list) and len(enable) != 5:
                raise ValueError('enable list must contain 5 values')
            for i in self._enable:
                try:
                    en = enable[i]
                    self._enable[i] = 1 if en else 0
                except KeyError:
                    pass

        if scaling is not None:
            checkvalue(scaling, -256, 255, 'scaling')
            self._scaling = scaling

        if offset is not None:
            checkvalue(offset, -256, 255, 'offset')
            self._offset = offset

        value_a = sum(c%64 << 6*(i-1) for (i, c) in self._coeffa.items())
        # aCoeffFilter does not contain a value for stage 0 --> (i-1)
        self._registerfile['aCoeffFilter_h'].set(value_a >> 15)
        self._registerfile['aCoeffFilter_l'].set(value_a & 0x7FFF)

        value_b = sum(c%64 << 6*i for (i, c) in self._coeffb.items())
        self._registerfile['bCoeffFilter_h'].set(value_b >> 15)
        self._registerfile['bCoeffFilter_l'].set(value_b & 0x7FFF)

        value_enable = sum(en << i for (i, en) in self._enable.items())
        self._registerfile['bypassFilterStage'].set((~value_enable) % 32)

        self._registerfile['offsetFilter'].set(self._offset % 512)
        self._registerfile['scalingFilter'].set(self._scaling % 512)

    def apply(self):
        self._registerfile['aCoeffFilter_h'].apply()
        self._registerfile['aCoeffFilter_l'].apply()
        self._registerfile['bCoeffFilter_h'].apply()
        self._registerfile['bCoeffFilter_l'].apply()
        self._registerfile['bypassFilterStage'].apply()
        self._registerfile['offsetFilter'].apply()
        self._registerfile['scalingFilter'].apply()

    def update(self):
        ra_h = self._registerfile['aCoeffFilter_h'].read() 
        ra_l = self._registerfile['aCoeffFilter_l'].read()
        ra = (ra_h << 15) + ra_l
        for i in self._coeffa:
            # aCoeffFilter does not contain a value for stage 0 --> (i-1)
            a = (ra >> (6*(i-1))) & 0x3F
            self._coeffa[i] = (a if a < 32 else a-64)

        rb_h = self._registerfile['bCoeffFilter_h'].read()
        rb_l = self._registerfile['bCoeffFilter_l'].read()
        rb = (rb_h << 15) + rb_l
        for i in self._coeffb:
            b = (rb >> (6*i)) & 0x3F
            self._coeffb[i] = (b if b < 32 else b-64)

        byp = self._registerfile['bypassFilterStage'].read()
        for i in self._enable:
            self._enable[i] = (~byp >> i) & 1

        scaling = self._registerfile['scalingFilter'].read()
        self._scaling = scaling if scaling < 256 else scaling-512

        offset = self._registerfile['offsetFilter'].read()
        self._offset = offset if offset < 256 else offset-512

    def get(self):
        return {'coeffa': self._coeffa,
                'coeffb': self._coeffb,
                'enable': self._enable,
                'scaling': self._scaling,
                'offset': self._offset}

    def __str__(self):
        s = ['                coeff. b: %4i  enabled: %s' %
             (self._coeffb[0], onoff(self._enable[0]))]
        s += ['coeff. a: %4i  coeff. b: %4i  enabled: %s' %
              (self._coeffa[i], self._coeffb[i], onoff(self._enable[i]))
              for i in range(1, 4)]
        s += ['scaling: %5i  offset: %6i  enabled: %s' %
             (self._scaling, self._offset, onoff(self._enable[4]))]
        return '\n'.join(s)


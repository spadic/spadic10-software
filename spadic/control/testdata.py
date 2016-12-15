from .base import *

_TESTDATAIN = 0
_TESTDATAOUT = 0
_TESTDATAGROUP = 0
class TestData(ControlUnitBase):
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

    def apply(self):
        self._registerfile['enableTestInput'].apply()
        self._registerfile['enableTestOutput'].apply()
        self._registerfile['testOutputSelGroup'].apply()

    def update(self):
        self._testdatain = self._registerfile['enableTestInput'].read()
        self._testdataout = self._registerfile['enableTestOutput'].read()
        self._group = self._registerfile['testOutputSelGroup'].read()

    def get(self):
        return {'testdatain': self._testdatain,
                'testdataout': self._testdataout,
                'group': {0: 'A', 1: 'B'}[self._group]}

    def __str__(self):
        return ('test data input: %s  test data output: %s  group: %s' %
                (onoff(self._testdatain), onoff(self._testdataout),
                 {0: 'A', 1: 'B'}[self._group]))


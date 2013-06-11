from led import Led
from hitlogic import HitLogic
from filter import Filter
from monitor import Monitor
from frontend import Frontend
from adcbias import AdcBias
from digital import Digital
from ui import SpadicControlUI

def frame(title, symbol='=', width=60):
    return '\n'.join(['#' + symbol*(width-1),
                      '# '+title,
                      '#' + symbol*(width-1)])

class SpadicController:
    """SPADIC 1.0 configuration controller.
    
    Contains the following control units:

    adcbias
    digital
    filter
    frontend
    hitlogic
    led
    monitor
    
    To get help on one of the units, type
      help(<name of controller variable>.<name of unit>)

    For example, if a Controller instance was created by
      c = Controller(...)
    and documentation about the hit logic settings is needed, type
      help(c.hitlogic)

    """
    def __init__(self, spadic, reset=0):
        self.registerfile = spadic._registerfile
        self.shiftregister = spadic._shiftregister

        # add control units
        self._units = {}
        self.led = Led(self.registerfile)
        self._units['LEDs'] = self.led
        self.hitlogic = HitLogic(self.registerfile)
        self._units['Hit logic'] = self.hitlogic
        self.filter = Filter(self.registerfile)
        self._units['Filter'] = self.filter
        self.monitor = Monitor(self.shiftregister)
        self._units['Monitor'] = self.monitor
        self.frontend = Frontend(self.shiftregister)
        self._units['Frontend'] = self.frontend
        self.adcbias = AdcBias(self.shiftregister)
        self._units['ADC bias'] = self.adcbias
        self.digital = Digital(self.registerfile)
        self._units['Digital'] = self.digital

        if reset:
            self.reset()
            self.apply()

        # bulk update faster than updates from controller
        self.registerfile.update()
        self.shiftregister.update()
        self.ui = SpadicControlUI(self, _log=spadic._debug_out)

    def reset(self):
        """Reset all control units."""
        for unit in self._units.itervalues():
            unit.reset()

    def apply(self):
        """Update register values from control units and write RF/SR."""
        for unit in self._units.itervalues():
            unit.apply()

    def update(self):
        """Read RF/SR and update control units from register values."""
        for unit in self._units.itervalues():
            unit.update()

    def __str__(self):
        return '\n\n'.join(frame(name)+'\n'+str(unit)
                           for (name, unit) in self._units.iteritems())

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
        for name in self.shiftregister.dict(nonzero):
            ln = name.ljust(25) + ' '
            sz = self.shiftregister.size(name)
            ln += fmtnumber(self.shiftregister[name], sz)
            srlines.append(ln)
        lines += sorted(srlines, key=str.lower)
        print >> f, '\n'.join(lines)

    def load(self, f):
        """Load the configuration from a text file.
        
        (not yet implemented)"""
        raise NotImplementedError


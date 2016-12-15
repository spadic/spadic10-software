import gzip
import os

from .led import Led
from .hitlogic import HitLogic
from .filter import Filter
from .monitor import Monitor
from .frontend import Frontend
from .adcbias import AdcBias
from .digital import Digital

AUTOSAVE_FILE = "/tmp/spadic/spadic_autosave.spc"

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
    def __init__(self, registerfile, shiftregister, reset=0, load_file=None):
        self.registerfile = registerfile
        self.shiftregister = shiftregister

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
        if load_file:
            self.load(load_file)
            self.update()

    def reset(self):
        """Reset all control units."""
        for unit in self._units.values():
            unit.reset()

    def apply(self):
        """Update register values from control units and write RF/SR."""
        for unit in self._units.values():
            unit.apply()

    def update(self):
        """Read RF/SR and update control units from register values."""
        # do this first, it is faster
        self.registerfile.update()
        self.shiftregister.update()
        for unit in self._units.values():
            unit.update()

    def __str__(self):
        return '\n\n'.join(frame(name)+'\n'+str(unit)
                           for (name, unit) in self._units.items())

    def save(self, filename=None, compress=True):
        filename = filename or AUTOSAVE_FILE
        if compress:
            filename += '.gz'
        save_dir = os.path.dirname(os.path.abspath(filename))
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        fopen = gzip.open if compress else open
        with fopen(filename, 'w') as f:
            self._save(f)

    def _save(self, f=None, nonzero=False):
        """Save the current configuration to a file."""
        def fmtnumber(n, sz):
            if sz == 1:
                fmt = '{0}'
            else:
                nhex = sz//4 + (1 if sz%4 else 0)
                fmt = '0x{:0'+str(nhex)+'X}'
            return fmt.format(n).rjust(6)
        lines = ['# Register file']
        rflines = []
        for name in self.registerfile:
            ln = name.ljust(25) + ' '
            sz = self.registerfile[name].size
            ln += fmtnumber(self.registerfile[name].get(), sz)
            rflines.append(ln)
        lines += sorted(rflines, key=str.lower)
        lines.append('# Shift register')
        srlines = []
        for name in self.shiftregister:
            ln = name.ljust(25) + ' '
            sz = self.shiftregister[name].size
            ln += fmtnumber(self.shiftregister[name].get(), sz)
            srlines.append(ln)
        lines += sorted(srlines, key=str.lower)
        print('\n'.join(lines), file=f)

    def load(self, filename):
        fopen = gzip.open if filename.endswith('.gz') else open
        with fopen(filename) as f:
            self._load(f)

    def _load(self, f):
        """Load the configuration from a file."""
        mode = None
        rf_values = {}
        sr_values = {}
        values = {'RF': rf_values, 'SR': sr_values}
        for line in f:
            if '# Register file' in line:
                mode = 'RF'
            elif '# Shift register' in line:
                mode = 'SR'
            else:
                if not mode:
                    continue
                content = line.partition('#')[0]
                if content.strip():
                    [name, value_str] = content.split()
                    value = int(value_str, 0)
                    values[mode][name] = value
        self.registerfile.set(rf_values)
        self.shiftregister.set(sr_values)
        self.registerfile.apply()
        self.shiftregister.apply()


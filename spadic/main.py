from . import ftdi_cbmnet
from .message import MessageSplitter
from .cbmnet import SpadicCbmnetRegisterAccess
from .registerfile import SpadicRegisterFile
from .shiftregister import SpadicShiftRegister
from .control import SpadicController

from . import Ftdi

class Spadic:
    """Representation of a SPADIC chip.

    Arguments:
    reset - flag for initial reset of the chip configuration
    load  - name of .spc configuration file to be loaded
    """

    from .util import log as _log
    def _debug(self, *text):
        self._log.info(' '.join(text))

    def __init__(self, reset=False, load=None, **kwargs):
        self._cbmif = ftdi_cbmnet.FtdiCbmnet(Ftdi.Ftdi())
        self._reg_access = SpadicCbmnetRegisterAccess(self._cbmif)
        self._splitters = [MessageSplitter(self._cbmif, lane)
                           for lane in [0, 1]]

        self.readout_enable(0)

        # higher level register file access
        def rf_write_gen(name, addr):
            def write(value):
                self._reg_access.write_registers([(addr, value)])
            return write
        def rf_read_gen(name, addr):
            def read():
                return next(self._reg_access.read_registers([addr]))
            return read
        self._registerfile = SpadicRegisterFile(rf_write_gen, rf_read_gen)

        # higher level shift register access
        self._shiftregister = SpadicShiftRegister(
            self._reg_access.write_registers, self._reg_access.read_registers)

        # highest level configuration controller
        self.control = SpadicController(self._registerfile,
                                        self._shiftregister, reset, load)

        self.readout_enable(1)

    def __enter__(self):
        self._cbmif.__enter__()
        self._reg_access.__enter__()
        for s in self._splitters:
            s.__enter__()
        return self

    def __exit__(self, *args):
        for s in self._splitters:
            s.__exit__()
        self._reg_access.__exit__()
        self._cbmif.__exit__(*args)

    def send_command(self, value):
        """Send the command with the given value."""
        self._cbmif.send_dlm(value)

    def readout_enable(self, enable):
        """Start or stop data taking in the chip."""
        dlm = 8 if enable else 9
        self.send_command(dlm)

    #----------------------------------------------------------------
    # read messages from groups A and B
    #----------------------------------------------------------------
    def read_groupA(self, timeout=1, raw=False):
        """Get one message from group A, if available."""
        return self._splitters[0].read_message(timeout, raw)

    def read_groupB(self, timeout=1, raw=False):
        """Get one message from group B, if available."""
        return self._splitters[1].read_message(timeout, raw)

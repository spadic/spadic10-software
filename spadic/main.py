from . import ftdi_stsxyter
from .message import MessageSplitter
from .stsxyter import SpadicStsxyterRegisterAccess
from .registerfile import SpadicRegisterFile, SPADIC20_RF
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
        self._interface = ftdi_stsxyter.FtdiStsxyter(Ftdi.Ftdi())
        self._reg_access = SpadicStsxyterRegisterAccess(
            self._interface, chip_address=7
        ) # TODO do not hard-code chip address
        self._splitters = [MessageSplitter(self._interface, lane)
                           for lane in [0, 1]]

        # higher level register file access
        def rf_write_gen(name, addr):
            def write(value):
                self._reg_access.write_registers([(addr, value)])
            return write
        def rf_read_gen(name, addr):
            def read():
                return next(self._reg_access.read_registers([addr]))
            return read
        self._registerfile = SpadicRegisterFile(
            rf_write_gen, rf_read_gen, register_map=SPADIC20_RF
        )

        # higher level shift register access
        self._shiftregister = SpadicShiftRegister(
            self._reg_access.write_registers, self._reg_access.read_registers)

        self.readout_enable(0)

        # highest level configuration controller
        self.control = SpadicController(self._registerfile,
                                        self._shiftregister, reset, load)

        self.readout_enable(1)

    def __enter__(self):
        self._interface.__enter__()
        self._reg_access.__enter__()
        for s in self._splitters:
            s.__enter__()
        return self

    def __exit__(self, *args):
        for s in self._splitters:
            s.__exit__()
        self._reg_access.__exit__()
        self._interface.__exit__(*args)

    def send_command(self, value):
        """Send the command with the given value."""
        raise NotImplementedError # TODO

    def readout_enable(self, enable):
        """Start or stop data taking in the chip."""
        self._registerfile['readoutEnabled'].write(1 if enable else 0)

    #----------------------------------------------------------------
    # read messages from groups A and B
    #----------------------------------------------------------------
    def read_groupA(self, timeout=1, raw=False):
        """Get one message from group A, if available."""
        return self._splitters[0].read_message(timeout, raw)

    def read_groupB(self, timeout=1, raw=False):
        """Get one message from group B, if available."""
        return self._splitters[1].read_message(timeout, raw)

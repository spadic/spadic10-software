from . import Ftdi
from .util import StreamDemultiplexer

from collections import namedtuple
import struct

# CBMnet interface packet consisting of
# addr: Address of the CBMnet send port
# words: List of 16-bit words
FtdiCbmnetPacket = namedtuple('FtdiCbmnetPacket', 'addr words')

# CBMnet interface port addresses
ADDR_DLM    = 0
ADDR_CTRL   = 1
ADDR_DATA_A = 2
ADDR_DATA_B = 3

# writable CBMnet interface ports and appropriate number of words
WRITE_LEN = {
  ADDR_DLM : 1,
  ADDR_CTRL: 3
}


class FtdiCbmnetInterface:
    """Representation of the FTDI <-> CBMnet interface."""

    from .util import log as _log
    def _debug(self, *text):
        self._log.info(' '.join(text)) # TODO use proper log levels

    def __init__(self):
        """Prepare FTDI connection."""
        self._ftdi = Ftdi.Ftdi()
        self._debug('init')

    def __enter__(self):
        """Open FTDI connection."""
        self._ftdi.__enter__()
        self._debug('enter')
        return self

    def __exit__(self, *args):
        """Close FTDI connection."""
        self._ftdi.__exit__(*args)
        self._debug('exit')

    def write(self, packet):
        """Write a packet to the CBMnet send interface."""
        packet = FtdiCbmnetPacket(*packet)
        if packet.addr not in WRITE_LEN:
            raise ValueError('Cannot write to this CBMnet port.')
        if len(packet.words) != WRITE_LEN[packet.addr]:
            raise ValueError('Wrong number of words for this CBMnet port.')

        self._debug('write', '%i,' % packet.addr,
                    '[%s]' % (' '.join('%04X' % w for w in packet.words)))

        header = struct.pack('BB', packet.addr, len(packet.words))
        data = struct.pack('>%dH' % len(packet.words), *packet.words)
        ftdi_data = header + data
        self._ftdi.write(ftdi_data)

    def read(self):
        """Read a packet from the CBMnet receive interface.

        If successful, return an FtdiCbmnetPacket instance.
        Otherwise, return None.
        """
        header = self._ftdi.read(2, max_iter=1)
        if len(header) < 2:
            return None

        addr, num_words = struct.unpack('BB', header)
        data = self._ftdi.read(2 * num_words)
        words = struct.unpack('>%dH' % num_words, data)

        self._debug('read', '%i,' % addr,
                    '[%s]' % (' '.join('%04X' % w for w in words)))

        return FtdiCbmnetPacket(addr, words)


class FtdiCbmnet:
    """Representation of the CBMnet interface over FTDI."""

    from .util import log as _log
    def _debug(self, *text):
        self._log.info(' '.join(text)) # TODO use proper log levels

    def __init__(self):
        self._demux = StreamDemultiplexer(
            interface=FtdiCbmnetInterface(),
            keys=[ADDR_DATA_A, ADDR_DATA_B, ADDR_CTRL]
        )
        self._debug('init')

    def __enter__(self):
        self._demux.__enter__()
        self._debug('enter')
        return self

    def __exit__(self, *args):
        self._demux.__exit__()
        self._debug('exit')

    def write_ctrl(self, words):
        """Write words to the control port of the CBMnet send interface."""
        self._demux.write(ADDR_CTRL, words)

    def write_command(self, words):
        """Write words to the command port of the CBMnet send interface."""
        self._demux.write(ADDR_DLM, words)

    def read_data(self, lane, timeout=1):
        """Read words from the CBMnet data receive interface at the given lane
        number.
        """
        addr = [ADDR_DATA_A, ADDR_DATA_B][lane]
        return self._demux.read(addr, timeout)

    def read_ctrl(self, timeout=1):
        """Read words from the CBMnet control receive interface."""
        return self._demux.read(ADDR_CTRL, timeout)

from . import stsxyter_frame
from .Ftdi import FtdiContainer
from .mux_stream import (
    MultiplexedStreamInterface, StreamDemultiplexer, NoDataAvailable
)


class NoUplinkFrame(ValueError):
    """Raised when bytes don't contain any known uplink frame."""
    pass


class FtdiStsxyterInterface(FtdiContainer, MultiplexedStreamInterface):
    """Representation of the FTDI <-> STS-XYTER protocol interface."""

    _uplink_frame_types = [
        ('HIT', stsxyter_frame.UplinkSpadicData),
        ('ACK', stsxyter_frame.UplinkAck),
        ('READ', stsxyter_frame.UplinkReadData)
    ]

    def write(self, value, destination=None):
        """Send a downlink frame over FTDI."""
        downlink_frame = value
        self._debug('write {}'.format(downlink_frame))
        self._ftdi.write(bytes(downlink_frame))

    def read(self):
        """Read an uplink frame over FTDI.

        If successful, return a pair (frame type, frame).
        Otherwise, raise NoDataAvailable.
        """
        def convert(data):
            for name, type_ in self._uplink_frame_types:
                try:
                    return name, type_.from_bytes(data, 'big')
                except stsxyter_frame.PrefixError:
                    continue
            else:
                raise NoUplinkFrame('Bytes contain no uplink frame: {!r}'
                                    .format(data))

        data = self._ftdi.read(3, max_iter=1)
        if not data:
            raise NoDataAvailable
        try:
            type_name, frame = convert(data)
        except NoUplinkFrame:
            raise NoDataAvailable

        self._debug('read {}'.format(frame))
        return type_name, frame


class FtdiStsxyter:
    """Representation of the STS-XYTER interface over FTDI."""

    from .util import log as _log
    def _debug(self, *text):
        self._log.info(' '.join(text)) # TODO use proper log levels

    def __init__(self, ftdi):
        self._demux = StreamDemultiplexer(
            interface=FtdiStsxyterInterface(ftdi),
            sources=[tp for tp, _ in FtdiStsxyterInterface._uplink_frame_types]
        )
        self._debug('init')

    def __enter__(self):
        self._demux.__enter__()
        self._debug('enter')
        return self

    def __exit__(self, *args):
        self._demux.__exit__()
        self._debug('exit')

    def write(self, frame):
        """Send a downlink frame over FTDI."""
        self._demux.write(frame)

    def read_data(self, lane, timeout=1):
        """Return a list containing a single message word contained in a hit
        frame read from the STS-XYTER interface at the given lane number.
        """
        # TODO support "lanes" A and B (need to implement in firmware first)
        if lane != 0:
            return None

        frame = self._demux.read('HIT', timeout)
        if frame is None:
            return None
        return [int(frame.word)]

    def read_ack(self, timeout=1):
        """Read an Ack frame from the STS-XYTER interface."""
        return self._demux.read('ACK', timeout)

    def read_reg_data(self, timeout=1):
        """Read a RDdata_ack frame from the STS-XYTER interface."""
        return self._demux.read('READ', timeout)

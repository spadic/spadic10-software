from . import stsxyter_frame
from .Ftdi import FtdiContainer
from .mux_stream import MultiplexedStreamInterface, NoDataAvailable


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
        self._debug('write {!r}'.format(downlink_frame))
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

        self._debug('read {!r}'.format(frame))
        return type_name, frame

from . import stsxyter_frame


class NoUplinkFrame(ValueError):
    """Raised when bytes don't contain any known uplink frame."""
    pass

def convert_uplink_frame(bytes_):
    """Given an array of 3 bytes, return the contained uplink frame.

    If no type of uplink frame matches the data, raise NoUplinkFrame.
    """
    for frame_type in [
        stsxyter_frame.UplinkSpadicData,
        stsxyter_frame.UplinkAck,
        stsxyter_frame.UplinkReadData
    ]:
        try:
            return frame_type.from_bytes(bytes_, 'big')
        except stsxyter_frame.PrefixError:
            continue
    else:
        raise NoUplinkFrame('Bytes contain no uplink frame: {!r}'
                            .format(bytes_))

def read_uplink_frame(ftdi):
    """Given an Ftdi instance, read bytes and return contained frames."""
    return convert_uplink_frame(ftdi.read(3))

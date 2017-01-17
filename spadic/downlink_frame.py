from .bits import Bits
from . import crc

DOWNLINK_CRC_POLY = crc.Polynomial(
    value=0x62cc, degree=15,
    representation=crc.PolyRepresentation.REVERSED_RECIPROCAL)


def calc_crc(data):
    """Calculate the 15-bit CRC for 25 bits of downlink frame data."""
    assert len(data) == 25
    return crc.crc(data, poly=DOWNLINK_CRC_POLY)


def has_correct_crc(frame):
    """Return True iff the 15-bit CRC contained in the 40-bit frame is
    correct."""
    assert len(frame) == 40
    return int(crc.crc(frame, poly=DOWNLINK_CRC_POLY)) == 0


def downlink_frame(chip_address, sequence_number, request_type, payload):
    """Calculate the 40-bit downlink frame as a single numeric value.

    >>> frame = downlink_frame(
    ...     chip_address=9, sequence_number=7, request_type=2, payload=0x7654
    ... )
    >>> '{:040b}'.format(frame)[:25]
    '1001011110111011001010100'
    """
    data = Bits()
    data.extend(Bits(chip_address, size=4))
    data.extend(Bits(sequence_number, size=4))
    data.extend(Bits(request_type, size=2))
    data.extend(Bits(payload, size=15))

    frame = data
    frame.extend(calc_crc(data))
    assert has_correct_crc(frame)
    return int(frame)


def split_words(frame):
    """Generate 5 bytes by splitting the 40-bit frame (MSB-first).

    >>> ['{:02x}'.format(w) for w in split_words(0x6789ABCDEF)]
    ['67', '89', 'ab', 'cd', 'ef']
    """
    for _ in range(5):
        yield (frame >> 32) % (1 << 8)
        frame <<= 8

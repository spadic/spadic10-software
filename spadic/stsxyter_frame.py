from abc import abstractproperty

from . import crc
from .bits import Bits, BitField


class BitFieldSuffixCRC(BitField):
    """A bit field with an additional CRC suffix.

    Concrete classes must define an attribute "_crc_poly" which is an instance
    of crc.Polynomial.
    """
    _crc_poly = abstractproperty()

    @classmethod
    def size(cls):
        return super().size() + cls._crc_poly.degree

    @classmethod
    def _calc_crc(cls, data):
        return crc.crc(data, poly=cls._crc_poly)

    def __new__(cls, *args, crc=None, **kwargs):
        instance = super().__new__(cls, *args, **kwargs)
        if crc is None:
            crc = cls._calc_crc(super().to_bits(instance))
        else:
            crc = Bits(int(crc), cls._crc_poly.degree)
        instance.crc = crc
        return instance

    def to_bits(self):
        """All fields including CRC concatenated to bits."""
        result = super().to_bits()
        result.extend(self.crc)
        return result

    @property
    def crc_is_correct(self):
        """True iff the CRC matches the contents of the bit field."""
        return int(self._calc_crc(self.to_bits())) == 0

    @classmethod
    def from_bits(cls, bits):
        """Return an instance given all bits (including the CRC)."""
        bits = bits.copy()
        crc_bits = bits.split(cls._crc_poly.degree)
        data = super().from_bits(bits)
        return cls(*data, crc=crc_bits)

#---------------------------------------------------------------------

class DownlinkFrame(BitFieldSuffixCRC):
    """A downlink frame with 5 bytes or 40 bits.

    >>> '{:010x}'.format(int(DownlinkFrame(
    ...     chip_address=9, sequence_number=7,
    ...     request_type=2, payload=0x7654
    ... ).to_bits()))
    '97bb2a615c'

    >>> f = DownlinkFrame.from_bits(Bits(0x97bb2a615c, 40))
    >>> int(f.chip_address)
    9
    >>> hex(f.payload)
    '0x7654'
    >>> f.crc_is_correct
    True
    """
    _fields = [
        ('chip_address', 4),
        ('sequence_number', 4),
        ('request_type', 2),
        ('payload', 15)
    ]

    _crc_poly = crc.Polynomial(
        value=0x62cc, degree=15,
        representation=crc.PolyRepresentation.REVERSED_RECIPROCAL
    )

    def __bytes__(self):
        """The 40-bit data (including CRC) of the downlink frame as a bytes
        object.

        >>> bytes(DownlinkFrame(
        ...     chip_address=9, sequence_number=7,
        ...     request_type=2, payload=0x7654
        ... )).hex()
        '97bb2a615c'
        """
        return self.to_bytes(byteorder='big')

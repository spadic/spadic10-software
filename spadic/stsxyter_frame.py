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

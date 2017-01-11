from copy import copy
from enum import Enum

from .bits import Bits


class PolyRepresentation(Enum):
    NORMAL = 1
    REVERSED = 2
    REVERSED_RECIPROCAL = 3
    KOOPMAN = REVERSED_RECIPROCAL


class Polynomial:
    """A polynomial used for CRC calculations."""

    def __init__(self, value, size,
                       representation=PolyRepresentation.REVERSED_RECIPROCAL):
        if representation not in PolyRepresentation:
            raise ValueError('Unknown representation: {}'
                             .format(representation))
        self._bits = Bits(value, size)
        self.representation = representation

    def __repr__(self):
        return (
            self.__class__.__name__
            + '(value={!r}, size={!r}, representation={!r}'
              .format(self._bits.value, self._bits.size, self.representation)
        )

    def normalized(self):
        """Return an equivalent polynomial in the normal representation.

        See https://en.wikipedia.org/wiki/Cyclic_redundancy_check#Specification
        and https://en.wikipedia.org/wiki/Mathematics_of_cyclic_redundancy_checks#Polynomial_representations

        >>> '{:04b}'.format(Polynomial(0b0011, 4, PolyRepresentation.NORMAL)
        ...                 .normalized()._bits.value)
        '0011'
        >>> '{:04b}'.format(Polynomial(0b1010, 4, PolyRepresentation.REVERSED)
        ...                 .normalized()._bits.value)
        '0101'
        >>> '{:04b}'.format(Polynomial(0b1100, 4, PolyRepresentation.KOOPMAN)
        ...                 .normalized()._bits.value)
        '1001'
        """
        src = self.representation
        if src is PolyRepresentation.NORMAL:
            return self
        elif src is PolyRepresentation.REVERSED:
            new_bits = self._bits.reversed()
        elif src is PolyRepresentation.REVERSED_RECIPROCAL:
            new_bits = copy(self._bits)
            new_bits.popleft(1)
            new_bits.append(Bits(1, 1))
        else:
            assert False, 'Forgot to implement a representation.'
        return Polynomial(new_bits.value, new_bits.size,
                          PolyRepresentation.NORMAL)


def crc(data, poly, init='1'):
    """Calculate the CRC value of the data using the given polynomial.

    >>> p = Polynomial(value=0x62cc, size=15)  # known as CRC-15-CAN
    >>> '{:04x}'.format(crc(data=Bits(value=0x00384c0, size=25), poly=p).value)
    '007c'
    """
    poly = poly.normalized()

    if init == '1':
        init = 2 ** poly._bits.size - 1
        assert '{:b}'.format(init) == '1' * poly._bits.size

    reg = Bits(init, poly._bits.size)

    for i in reversed(range(data.size)):
        high_bit = reg.popleft(1).value ^ data[i]
        reg.append(Bits(value=0, size=1))
        if high_bit:
            reg.value ^= poly._bits.value

    return reg

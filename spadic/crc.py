from collections import namedtuple
from enum import Enum


def get_bit(value, position):
    """Return the digit of the binary representation of the value at the given
    position, where position 0 is the LSB.

    >>> [get_bit(0b1101, position=i) for i in reversed(range(4))]
    [1, 1, 0, 1]
    """
    return (value >> position) & 1


def reverse_bits(value, bits):
    """Return the value obtained by reversing the binary representation.

    >>> '{:04b}'.format(reverse_bits(0b1101, 4))
    '1011'
    """
    return sum(2 ** i * get_bit(value, bits - i - 1)
               for i in range(bits))


class PolyRepresentation(Enum):
    NORMAL = 1
    REVERSED = 2
    REVERSED_RECIPROCAL = 3
    KOOPMAN = REVERSED_RECIPROCAL


class Polynomial(namedtuple('PolynomialRecord', 'value bits representation')):
    """A polynomial used for CRC calculations."""

    def __new__(cls, value, bits,
                     representation=PolyRepresentation.REVERSED_RECIPROCAL):
        if representation not in PolyRepresentation:
            raise ValueError('Unknown representation: {}'
                             .format(representation))
        return super().__new__(cls, value % (2 ** bits), bits, representation)

    def normalized(self):
        """Return an equivalent polynomial in the normal representation.

        See https://en.wikipedia.org/wiki/Cyclic_redundancy_check#Specification
        and https://en.wikipedia.org/wiki/Mathematics_of_cyclic_redundancy_checks#Polynomial_representations

        >>> '{:04b}'.format(Polynomial(0b0011, 4, PolyRepresentation.NORMAL)
        ...                 .normalized().value)
        '0011'
        >>> '{:04b}'.format(Polynomial(0b1010, 4, PolyRepresentation.REVERSED)
        ...                 .normalized().value)
        '0101'
        >>> '{:04b}'.format(Polynomial(0b1100, 4, PolyRepresentation.KOOPMAN)
        ...                 .normalized().value)
        '1001'
        """
        src = self.representation
        if src is PolyRepresentation.NORMAL:
            return self
        elif src is PolyRepresentation.REVERSED:
            value = reverse_bits(self.value, self.bits)
        elif src is PolyRepresentation.REVERSED_RECIPROCAL:
            value = ((self.value << 1) % (2 ** self.bits)) + 1
        else:
            assert False, 'Forgot to implement a representation.'
        return Polynomial(value, self.bits, PolyRepresentation.NORMAL)


def crc(data, data_bits, poly, init='1'):
    """Calculate the CRC value of the data using the given polynomial.

    >>> p = Polynomial(value=0x62cc, bits=15)  # known as CRC-15-CAN
    >>> '{:04x}'.format(crc(data=0x00384c0, data_bits=25, poly=p))
    '007c'
    """
    poly = poly.normalized()

    if init == '1':
        reg = 2 ** poly.bits - 1
        assert '{:b}'.format(reg) == '1' * poly.bits
    else:
        reg = init

    for i in reversed(range(data_bits)):
        high_bit = get_bit(reg, poly.bits - 1) ^ get_bit(data, i)
        reg <<= 1
        if high_bit:
            reg ^= poly.value

    return reg % (2 ** poly.bits)

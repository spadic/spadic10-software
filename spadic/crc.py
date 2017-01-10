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


def normalize_poly(value, bits, src=PolyRepresentation.REVERSED_RECIPROCAL):
    """Convert a polynomial from any source representation to the normal
    representation.

    See https://en.wikipedia.org/wiki/Cyclic_redundancy_check#Specification
    and https://en.wikipedia.org/wiki/Mathematics_of_cyclic_redundancy_checks#Polynomial_representations

    >>> '{:04b}'.format(normalize_poly(0b0011, 4, PolyRepresentation.NORMAL))
    '0011'
    >>> '{:04b}'.format(normalize_poly(0b1010, 4, PolyRepresentation.REVERSED))
    '0101'
    >>> '{:04b}'.format(normalize_poly(0b1100, 4, PolyRepresentation.KOOPMAN))
    '1001'
    """
    if src is PolyRepresentation.NORMAL:
        return value % (2 ** bits)
    elif src is PolyRepresentation.REVERSED:
        return reverse_bits(value, bits)
    elif src is PolyRepresentation.REVERSED_RECIPROCAL:
        return ((value << 1) % (2 ** bits)) + 1
    else:
        raise ValueError('Unknown representation: {}'.format(src))


def crc(data, data_bits, poly, poly_bits, init='1'):
    """Calculate the CRC value of the data using the given polynomial in normal
    representation.

    >>> p = normalize_poly(value=0x62cc, bits=15)  # known as CRC-15-CAN
    >>> '{:04x}'.format(crc(data=0x00384c0, data_bits=25,
    ...                     poly=p, poly_bits=15))
    '007c'
    """
    if init == '1':
        reg = 2 ** poly_bits - 1
        assert '{:b}'.format(reg) == '1' * poly_bits
    else:
        reg = init

    for i in reversed(range(data_bits)):
        high_bit = get_bit(reg, poly_bits - 1) ^ get_bit(data, i)
        reg <<= 1
        if high_bit:
            reg ^= poly

    return reg % (2 ** poly_bits)

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
    result = 0
    for i in range(bits):
        result += 2 ** i * get_bit(value, bits - i - 1)
    return result


def make_poly(value, bits, representation='reversed reciprocal'):
    """Convert different numerical representations of a polynomial to
    a canonical ('normal') representation.

    See https://en.wikipedia.org/wiki/Cyclic_redundancy_check#Specification
    and https://en.wikipedia.org/wiki/Mathematics_of_cyclic_redundancy_checks#Polynomial_representations

    >>> '{:04b}'.format(make_poly(0b0011, 4, 'normal'))
    '0011'
    >>> '{:04b}'.format(make_poly(0b1010, 4, 'reversed'))
    '0101'
    >>> '{:04b}'.format(make_poly(0b1100, 4, 'reversed reciprocal'))
    '1001'
    """
    if representation == 'normal':
        return value % (2 ** bits)
    elif representation == 'reversed':
        return reverse_bits(value, bits)
    elif representation in ['reversed reciprocal', 'koopman']:
        return ((value << 1) % (2 ** bits)) + 1
    else:
        raise NotImplementedError(
            'Unknown representation: {}'.format(representation))


def crc(data, data_bits, poly, poly_bits, init='1'):
    """Calculate the CRC value of the data using the given polynomial in normal
    representation.

    >>> p = make_poly(value=0x62cc, bits=15)  # known as CRC-15-CAN
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

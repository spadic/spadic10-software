def get_bit(value, position):
    """
    >>> [get_bit(0b1101, position=i) for i in reversed(range(4))]
    [1, 1, 0, 1]
    """

    return (value >> position) & 1


def reverse_bits(value, bits):
    """
    >>> bin(reverse_bits(0b1101, 4))
    '0b1011'
    """
    result = 0
    for i in range(bits):
        result += 2 ** i * get_bit(value, bits - i - 1)
    return result


def make_poly(value, bits, representation='reversed reciprocal'):
    if representation == 'normal':
        return value % (2 ** bits)
    elif representation == 'reversed':
        return reverse_bits(value, bits)
    elif representation == 'reversed reciprocal':
        return ((value << 1) % (2 ** bits)) + 1
    else:
        raise NotImplementedError(representation)


def crc(data, data_bits, poly, poly_bits, init='1'):
    """
    >>> poly = make_poly(value=0x62cc, bits=15)
    >>> crc(data=0x00384c0, data_bits=25, poly=poly, poly_bits=15, init='1')
    0x007c
    """

    if init == '1':
        reg = 2 ** poly_bits - 1
    else:
        reg = init

    for i in range(data_bits):
        high_bit = get_bit(reg, poly_bits - 1) ^ get_bit(data, i)
        reg <<= 1
        if high_bit:
            reg ^= poly

    return reg % (2 ** poly_bits)

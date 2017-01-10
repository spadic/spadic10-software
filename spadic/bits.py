from numbers import Integral

def _plural_bits(n):
    return '1 bit' if n == 1 else '{} bits'.format(n)

class Bits:
    """Represent integer values as a sequence of bits."""

    def __init__(self, value=0, size=None):
        """Initialize instance with given integer value and number of bits.

        If size is left unspecified, the minimum number of bits necessary to
        represent the value is used.
        """
        if size is None:
            size = value.bit_length()
        for x in [value, size]:
            if not isinstance(x, Integral):
                raise TypeError('Expected integer argument: {}'.format(x))
        if size < 0:
            raise ValueError('Size must not be negative.')
        if value < 0:
            raise ValueError('Cannot represent negative values.')
        elif value >= 2 ** size:
            raise ValueError('Cannot represent {} using {}.'
                             .format(value, _plural_bits(size)))
        self.value, self.size = value, size

    def append(self, other):
        """Append other bits to the right.

        >>> b = Bits(0x3, 2)
        >>> b.append(Bits(0x10, 8))
        >>> hex(b.value)
        '0x310'
        """
        self.value = (self.value << other.size) + other.value
        self.size += other.size

    def popleft(self, n):
        """Remove and return the n leftmost bits.

        >>> b = Bits(0x310, 12)
        >>> b.popleft(4)
        Bits(value=3, size=4)
        >>> b
        Bits(value=16, size=8)
        """
        remaining_size = self.size - n
        if remaining_size < 0:
            raise ValueError('Cannot split {} from {}-bit value.'
                             .format(_plural_bits(n), self.size))

        result_value = (self.value >> remaining_size) % (1 << n)
        self.value %= (1 << remaining_size)
        self.size = remaining_size
        return Bits(result_value, n)

    def __repr__(self):
        return '{}(value={!r}, size={!r})'.format(
            self.__class__.__name__, self.value, self.size)

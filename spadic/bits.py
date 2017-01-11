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
        self._value, self._size = value, size

    def __getitem__(self, i):
        """Return the i'th bit from the right (i = 0 -> LSB).

        >>> b = Bits(0b1101, 4)
        >>> [b[i] for i in reversed(range(4))]
        [1, 1, 0, 1]
        """
        if self._size == 0 or i >= self._size:
            raise IndexError('Bad index for {}-bit value: {}'
                             .format(self._size, i))
        i %= self._size  # support negative indexes
        return (self._value >> i) & 1

    def __len__(self):
        """Return the number of bits."""
        return self._size

    def __int__(self):
        """Return the integer value of the bits."""
        return self._value

    def reversed(self):
        """Return a reversed copy of the bits.

        >>> b = Bits(0b1101, 4).reversed()
        >>> '{:04b}'.format(int(b))
        '1011'
        """
        value = sum(2 ** i * self[self._size - i - 1]
                    for i in range(self._size))
        return Bits(value, self._size)

    def append(self, other):
        """Append other bits to the right.

        >>> b = Bits(0x3, 2)
        >>> b.append(Bits(0x10, 8))
        >>> hex(int(b))
        '0x310'
        >>> len(b)
        10
        """
        self._value = (self._value << len(other)) + int(other)
        self._size += len(other)

    def popleft(self, n):
        """Remove and return the n leftmost bits.

        >>> b = Bits(0x310, 12)
        >>> b.popleft(4)
        Bits(value=3, size=4)
        >>> b
        Bits(value=16, size=8)
        """
        remaining_size = self._size - n
        if remaining_size < 0:
            raise ValueError('Cannot split {} from {}-bit value.'
                             .format(_plural_bits(n), self._size))

        result_value = (self._value >> remaining_size) % (1 << n)
        self._value %= (1 << remaining_size)
        self._size = remaining_size
        return Bits(result_value, n)

    def __repr__(self):
        return '{}(value={!r}, size={!r})'.format(
            self.__class__.__name__, self._value, self._size)

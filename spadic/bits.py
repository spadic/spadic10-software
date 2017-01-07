class Bits:
    """Represent integer values as a sequence of bits."""

    def __init__(self, value=0, size=None):
        """Initialize instance with given integer value and number of bits.

        If size is left unspecified, the minimum number of bits necessary to
        represent the value is used.
        """
        if size is None:
            size = value.bit_length()
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
            raise ValueError('Cannot split {} bits from {}-bit value.'
                             .format(n, self.size))

        result_value = (self.value >> remaining_size) % (1 << n)
        self.value %= (1 << remaining_size)
        self.size = remaining_size
        return Bits(result_value, n)

    def __repr__(self):
        return '{}(value={!r}, size={!r})'.format(
            self.__class__.__name__, self.value, self.size)

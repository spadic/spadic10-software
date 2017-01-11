from collections.abc import Sequence
from numbers import Integral

def _plural_bits(n):
    return '1 bit' if n == 1 else '{} bits'.format(n)

class Bits(Sequence):
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

    @classmethod
    def all_ones(cls, n):
        """Return the n-bit value where every bit is 1.

        >>> b = Bits.all_ones(5)
        >>> len(b)
        5
        >>> bin(b)
        '0b11111'
        """
        return cls(value=2 ** n - 1, size=n)

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

    @property
    def msb(self):
        """Return the most significant bit.

        >>> Bits(0b1000, 4).msb
        1
        >>> Bits(0b0111, 4).msb
        0
        """
        return self[-1]

    @property
    def lsb(self):
        """Return the least significant bit.

        >>> Bits(0b0001, 4).lsb
        1
        >>> Bits(0b1110, 4).lsb
        0
        """
        return self[0]

    def __len__(self):
        """Return the number of bits."""
        return self._size

    def __int__(self):
        """Return the integer value of the bits."""
        return self._value

    def __index__(self):
        """Support hex(), bin(), etc."""
        return self.__int__()

    def __xor__(self, other):
        """Return self ^ other.

        Integer arguments are implicitly converted to Bits.
        Argument must not have more bits than self.
        """
        if isinstance(other, Integral):
            other = Bits(other)
        if self._size < len(other):
            raise ValueError('Other operand has too many bits: {!r}'
                             .format(other))
        return Bits(self._value ^ int(other), self._size)

    def reversed(self):
        """Return a reversed copy of the bits.

        >>> b = Bits(0b1101, 4).reversed()
        >>> '{:04b}'.format(int(b))
        '1011'
        """
        value = sum(2 ** i * b for i, b in enumerate(reversed(self)))
        return Bits(value, self._size)

    def append(self, other):
        """Append other bits to the right.

        >>> b = Bits(0x3, 2)
        >>> b.append(Bits(0x10, 8))
        >>> hex(b)
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

    def to_bytes(self, byteorder):
        """Return a bytes object representing the bits.

        >>> b = Bits(value=0x1abc, size=13)
        >>> b.to_bytes(byteorder='big').hex()
        '1abc'
        >>> b.to_bytes(byteorder='little').hex()
        'bc1a'
        """
        num_bytes = -(-self._size // 8)  # rounding up
        return self._value.to_bytes(num_bytes, byteorder)

    def __repr__(self):
        return '{}(value={!r}, size={!r})'.format(
            self.__class__.__name__, self._value, self._size)

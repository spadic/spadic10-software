from abc import ABCMeta, abstractproperty
from collections import namedtuple, OrderedDict
from collections.abc import Sequence
from functools import lru_cache
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

    def copy(self):
        """Return a copy of self."""
        return Bits(value=self._value, size=self._size)

    @classmethod
    def all_ones(cls, n):
        """Return an instance with n bits where every bit is 1.

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
        >>> all(int(x) == sum(b * 2**i for i, b in enumerate(Bits(x, 4)))
        ...     for x in range(16))
        True
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
        """Return an instance with the bits in reverse order.

        >>> b = Bits(0b1011, 4).reversed()
        >>> b
        Bits(value=13, size=4)
        >>> '{:04b}'.format(int(b))
        '1101'
        """
        value = sum(2 ** i * b for i, b in enumerate(reversed(self)))
        return Bits(value, self._size)

    def extend(self, other):
        """Extend self on the right side by other bits.

        >>> b = Bits(0x3, 2)
        >>> b.extend(Bits(0x10, 8))
        >>> hex(b)
        '0x310'
        >>> len(b)
        10
        """
        self._value = (self._value << len(other)) + int(other)
        self._size += len(other)

    def append(self, bit):
        """Append a single bit on the right side.

        >>> b = Bits(0x3, 2)
        >>> b.append(1)
        >>> int(b)
        7
        >>> len(b)
        3
        """
        self.extend(Bits(int(bit), size=1))

    def splitleft(self, n):
        """Remove and return the n leftmost bits.

        >>> b = Bits(0x310, 12)
        >>> b.splitleft(4)
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

    def popleft(self):
        """Remove and return the leftmost bit.

        >>> b = Bits(value=4, size=3)
        >>> b.popleft()
        Bits(value=1, size=1)
        >>> b
        Bits(value=0, size=2)
        """
        return self.splitleft(1)

    def to_bytes(self, byteorder):
        """Return an array of bytes representing the bits.

        >>> b = Bits(value=0x1abc, size=13)
        >>> b.to_bytes(byteorder='big').hex()
        '1abc'
        >>> b.to_bytes(byteorder='little').hex()
        'bc1a'
        """
        num_bytes = -(-self._size // 8)  # rounding up
        return self._value.to_bytes(num_bytes, byteorder)

    @classmethod
    def from_bytes(cls, bytes, size, byteorder):
        """Create an instance with the given size from an array of bytes.

        >>> Bits.from_bytes(bytes([0xbc, 0x1a]), size=13, byteorder='little')
        Bits(value=6844, size=13)
        """
        return cls(value=int.from_bytes(bytes, byteorder), size=size)

    def __repr__(self):
        return '{}(value={!r}, size={!r})'.format(
            self.__class__.__name__, self._value, self._size)


# derived from http://code.activestate.com/recipes/577629-namedtupleabc
class _BitFieldMeta(ABCMeta):
    def __new__(mcls, name, bases, namespace):
        def find_fields(namespace, bases):
            """Look for a _fields attribute in the namespace or one of the base
            classes.
            """
            fields = namespace.get('_fields')
            for base in bases:
                if fields is not None:
                    break
                fields = getattr(base, '_fields', None)
            return fields

        def insert_namedtuple(name, bases, namespace):
            """Insert a namedtuple based on the given fields *after* the other
            base classes, so that calls to its methods can be intercepted.
            """
            fields = list(namespace['_fields'])
            basetuple = namedtuple('{}Fields'.format(name), fields)
            del basetuple._source  # is no longer accurate
            bases = bases + (basetuple,)
            namespace.setdefault('__doc__', basetuple.__doc__)
            namespace.setdefault('__slots__', ())
            return bases

        fields = find_fields(namespace, bases)
        if not isinstance(fields, abstractproperty):
            namespace['_fields'] = OrderedDict(fields)
            bases = insert_namedtuple(name, bases, namespace)
        return ABCMeta.__new__(mcls, name, bases, namespace)

    @property
    def _size(cls):
        """The total number of bits."""
        return sum(cls._fields.values())


class BitField(metaclass=_BitFieldMeta):
    """Abstract base class for bit fields, which are "namedtuples of Bits".

    Concrete classes must define an ordered (name -> size) mapping as the
    _fields attribute.
    """
    _fields = abstractproperty()

    def __new__(cls, *args, **kwargs):
        """Create an instance, promoting the arguments to Bits if cls is
        concrete. If cls is abstract, raise TypeError.
        """
        # "can't instantiate abstract class" TypeError is a feature of ABCMeta
        if not isinstance(cls._fields, abstractproperty):
            args = [
                Bits(int(value), size)
                for value, (name, size) in zip(args, cls._fields.items())
            ]
            kwargs = {
                name: Bits(int(value), size=cls._fields[name])
                for name, value in kwargs.items()
            }
        return super().__new__(cls, *args, **kwargs)

    @lru_cache(1)
    def to_bits(self):
        bits = Bits()
        for field in self:
            bits.extend(field)
        return bits

    @classmethod
    def from_bits(cls, bits):
        expected = cls._size
        if len(bits) != expected:
            raise ValueError('Expected {}: {}'
                             .format(_plural_bits(expected), bits))
        def fields():
            b = bits.copy()
            for size in cls._fields.values():
                yield b.splitleft(size)
        return cls(*fields())

    @lru_cache(2) # big, little
    def to_bytes(self, byteorder):
        return self.to_bits().to_bytes(byteorder)

    @classmethod
    def from_bytes(cls, bytes, byteorder):
        return cls.from_bits(Bits.from_bytes(bytes, cls._size, byteorder))

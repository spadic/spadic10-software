from abc import ABCMeta, abstractproperty
from collections import deque, namedtuple, OrderedDict
from collections.abc import Sequence
from numbers import Integral
import re

def _plural_bits(n):
    return '1 bit' if n == 1 else '{} bits'.format(n)

#---- Bits -----------------------------------------------------------

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

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._value == int(other) and self._size == len(other)

    def __ne__(self, other):
        return not self == other

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

    def _extend_value(self, other):
        return (self._value << len(other)) + int(other)

    def extend(self, other):
        """Extend self on the right side by other bits.

        >>> b = Bits(0x3, 2)
        >>> b.extend(Bits(0x10, 8))
        >>> hex(b)
        '0x310'
        >>> len(b)
        10
        """
        self._value = self._extend_value(other)
        self._size += len(other)

    def extendleft(self, other):
        """Extend self on the left side by other bits.

        >>> b = Bits(0x3, 2)
        >>> b.extendleft(Bits(0x10, 8))
        >>> hex(b)
        '0x43'
        >>> len(b)
        10
        """
        self._value = other._extend_value(self)
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

    def appendleft(self, bit):
        """Append a single bit on the left side.

        >>> b = Bits(0x2, 2)
        >>> b.appendleft(1)
        >>> int(b)
        6
        >>> len(b)
        3
        """
        self.extendleft(Bits(int(bit), size=1))

    def _splitleft(self, n):
        remaining_size = self._size - n
        if remaining_size < 0:
            raise ValueError('Cannot split {} from {}-bit value.'
                             .format(_plural_bits(n), self._size))

        left = (self._value >> remaining_size)
        right = self._value % (1 << remaining_size)
        return left, right, remaining_size

    def splitleft(self, n):
        """Remove and return the n leftmost bits.

        >>> b = Bits(0x310, 12)
        >>> b.splitleft(4)
        Bits(value=3, size=4)
        >>> b
        Bits(value=16, size=8)
        """
        left, right, remaining = self._splitleft(n)
        self._value, self._size = right, remaining
        return Bits(left, n)

    def split(self, n):
        """Remove and return the n rightmost bits.

        >>> b = Bits(0x310, 12)
        >>> b.split(4)
        Bits(value=0, size=4)
        >>> b
        Bits(value=49, size=8)
        """
        remaining = len(self) - n
        left, right, _ = self._splitleft(remaining)
        self._value, self._size = left, remaining
        return Bits(right, n)

    def popleft(self):
        """Remove and return the leftmost bit.

        >>> b = Bits(value=4, size=3)
        >>> b.popleft()
        Bits(value=1, size=1)
        >>> b
        Bits(value=0, size=2)
        """
        return self.splitleft(1)

    def pop(self):
        """Remove and return the rightmost bit.

        >>> b = Bits(value=4, size=3)
        >>> b.pop()
        Bits(value=0, size=1)
        >>> b
        Bits(value=2, size=2)
        """
        return self.split(1)

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
            type(self).__name__, self._value, self._size)

#---- BitField -------------------------------------------------------

# inspired by http://lucumr.pocoo.org/2015/11/18/pythons-hidden-re-gems/
def parse_fields(field_spec):
    """Parse the (name, size) pairs from a field specification string.

    Name and size can be separated by `:`, `=` or whitespace.
    Pairs can be separated by `,`, `;` or whitespace.

    >>> list(parse_fields('a: 3, b  5 ; c =6  '))
    [('a', 3), ('b', 5), ('c', 6)]
    """
    p = re.compile(r'''
        \s*
        (\w+) \s*[:=\s]\s* (\d+)  # (name, size) pair
        \s*
        (?: [,;\s]\s* | $ )       # separator between pairs or end
    ''', re.VERBOSE)
    sc = p.scanner(field_spec)
    match = None
    for match in iter(sc.match, None):
        name, size = match.groups()
        yield name, int(size)
    if not match or match.end() < len(field_spec):
        raise ValueError('Bad field formatting: {!r} (last match: {!r})'
                         .format(field_spec,
                                 getattr(match, 'group', lambda: None)()))

# derived from http://code.activestate.com/recipes/577629-namedtupleabc
class _BitFieldMeta(ABCMeta):
    def __new__(mcls, name, bases, namespace):
        def find_field_spec(namespace, bases):
            """Look for a _fields attribute in the namespace or one of the base
            classes.
            """
            field_spec = namespace.get('_fields')
            for base in bases:
                if field_spec is not None:
                    break
                field_spec = getattr(base, '_fields', None)
            return field_spec

        def insert_namedtuple(name, bases, namespace):
            """Insert a namedtuple based on the given fields *after* the other
            base classes, so that calls to its methods can be intercepted.
            """
            field_names = list(namespace['_fields'])
            basetuple = namedtuple('{}Fields'.format(name), field_names)
            del basetuple._source  # is no longer accurate
            bases = bases + (basetuple,)
            namespace.setdefault('__doc__', basetuple.__doc__)
            namespace.setdefault('__slots__', ())
            return bases

        field_spec = find_field_spec(namespace, bases)
        if not isinstance(field_spec, abstractproperty):
            try:
                namespace['_fields'] = OrderedDict(field_spec)
            except ValueError:
                namespace['_fields'] = OrderedDict(parse_fields(field_spec))
            bases = insert_namedtuple(name, bases, namespace)
        return ABCMeta.__new__(mcls, name, bases, namespace)

    @property
    def _fields_size(cls):
        """The number of bits in all fields."""
        return sum(cls._fields.values())


class BitField(metaclass=_BitFieldMeta):
    """Abstract base class for bit fields, which are "namedtuples of Bits".

    Concrete classes must have a _fields attribute defining an ordered
    (name -> size) mapping.

    _fields can be a formatted string, see help(parse_fields).

    Example usage:

    >>> class IPv4Header(BitField):
    ...     _fields = '''
    ...         version: 4, ihl: 4, dscp: 6, ecn: 2,
    ...         total_length: 16, identification: 16,
    ...         reserved_flag: 1, df_flag: 1, mf_flag: 1,
    ...         fragment_offset: 13, ttl: 8, protocol: 8,
    ...         checksum: 16, source_addr: 32, dest_addr: 32
    ...     '''
    ...
    >>> IPv4Header.size()
    160
    >>> # http://www.cs.miami.edu/home/burt/learning/Csc524.092/notes/ip_example.html
    >>> h = IPv4Header.from_bytes((int(x, 16)
    ...     for x in '45 00 00 44 ad 0b 00 00 40 11 72 72 ac 14 02 fd ac 14 00 06'.split()
    ... ), byteorder='big')
    ...
    >>> int(h.version)
    4
    >>> h.ttl
    Bits(value=64, size=8)
    >>> hex(h.protocol)
    '0x11'
    """
    _fields = abstractproperty()

    def __new__(cls, *args, **kwargs):
        """Create an instance, promoting the arguments to Bits if cls is
        concrete. If cls is abstract, raise TypeError.
        """
        # "can't instantiate abstract class" TypeError is a feature of ABCMeta

        def promote_args(args, kwargs, fields):
            """Return new args and kwargs where arguments that are fields are
            promoted to Bits and others are kept, so that handling of
            unexpected arguments can be left to namedtuple.

            >>> fields = OrderedDict([('a', 8), ('b', 9)])
            >>> promote_args([11, 12, 13], {}, fields)
            ([Bits(value=11, size=8), Bits(value=12, size=9), 13], {})
            >>> promote_args([11], dict(b=12, c=13), fields)
            ([Bits(value=11, size=8)], {'b': Bits(value=12, size=9), 'c': 13})
            """
            _args, remaining = list(), deque(args)
            for value, (name, size) in zip(args, fields.items()):
                _args.append(Bits(int(value), size))
                remaining.popleft()
            _args.extend(remaining)

            _kwargs = dict(kwargs)
            for name, value in kwargs.items():
                if name in fields:
                    _kwargs[name] = Bits(int(value), size=fields[name])

            return _args, _kwargs

        if not isinstance(cls._fields, abstractproperty):
            args, kwargs = promote_args(args, kwargs, cls._fields)

        return super().__new__(cls, *args, **kwargs)

    @classmethod
    def size(cls):
        """The total number of bits (may be overridden in subclasses)."""
        return cls._fields_size

    def to_bits(self):
        """Return a Bits instance representing the concatenated fields."""
        bits = Bits()
        for field in self:
            bits.extend(field)
        return bits

    @classmethod
    def from_bits(cls, bits):
        """Create an instance from the bits representing the concatenated
        fields.
        """
        expected = cls._fields_size
        if len(bits) != expected:
            raise ValueError('Expected {}: {}'
                             .format(_plural_bits(expected), bits))
        def fields():
            b = bits.copy()
            for size in cls._fields.values():
                yield b.splitleft(size)
        return cls(*fields())

    def to_bytes(self, byteorder):
        """Return an array of bytes representing the concatenated fields."""
        return self.to_bits().to_bytes(byteorder)

    @classmethod
    def from_bytes(cls, bytes, byteorder):
        """Create an instance from an array of bytes."""
        return cls.from_bits(Bits.from_bytes(bytes, cls.size(), byteorder))

    def __repr__(self):
        def format_field(name):
            return '{}={}'.format(name, int(getattr(self, name)))
        return '{name}({fields})'.format(
            name=type(self).__name__,
            fields=', '.join(map(format_field, self._fields.keys()))
        )

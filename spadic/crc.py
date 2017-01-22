from enum import Enum

from .bits import Bits


class PolyRepresentation(Enum):
    NORMAL = 1
    REVERSED = 2
    REVERSED_RECIPROCAL = 3
    KOOPMAN = REVERSED_RECIPROCAL


class Polynomial:
    """A polynomial used for CRC calculations."""

    def __init__(self, value, degree,
                       representation=PolyRepresentation.REVERSED_RECIPROCAL):
        """Initialize a polynomial given its degree and the characteristic
        value in a particular representation.

        See https://en.wikipedia.org/wiki/Cyclic_redundancy_check#Specification
        and https://en.wikipedia.org/wiki/Mathematics_of_cyclic_redundancy_checks#Polynomial_representations

        >>> '{:04b}'.format(int(Polynomial(0b0011, 4, PolyRepresentation.NORMAL)))
        '0011'
        >>> '{:04b}'.format(int(Polynomial(0b1010, 4, PolyRepresentation.REVERSED)))
        '0101'
        >>> '{:04b}'.format(int(Polynomial(0b1100, 4, PolyRepresentation.KOOPMAN)))
        '1001'
        """
        bits = Bits(value, degree)
        if representation not in PolyRepresentation:
            raise ValueError('Unknown representation: {}'
                             .format(representation))
        if degree > 0:
            # In each CRC polynomial, the coefficients for the x^0 and x^degree
            # terms must be 1. The integer value representing the polynomial
            # omits only one of those coefficients, while the other one is
            # redundant. Here it is checked that the redundant bit is also 1.
            bit, term = {
                PolyRepresentation.NORMAL: (bits.lsb, 0),
                PolyRepresentation.REVERSED: (bits.msb, 0),
                PolyRepresentation.REVERSED_RECIPROCAL: (bits.msb, degree)
            }[representation]
            if not bit:
                raise ValueError('Coefficient of x^{} term must be 1.'
                                 .format(term))

        if representation is PolyRepresentation.NORMAL:
            self._bits = bits
        elif representation is PolyRepresentation.REVERSED:
            self._bits = bits.reversed()
        elif representation is PolyRepresentation.REVERSED_RECIPROCAL:
            _bits = bits.copy()
            _bits.popleft()
            _bits.append(1)
            self._bits = _bits
        else:
            assert False, 'Forgot to implement a representation.'

    def __int__(self):
        return int(self._bits)

    def __index__(self):
        return self.__int__()

    @property
    def degree(self):
        """Degree of the polynomial, exponent of the highest term."""
        return len(self._bits)

    def __len__(self):
        """Number of terms in the polynomial. One higher than the degree."""
        return self.degree + 1

    def __repr__(self):
        return (
            self.__class__.__name__
            + '(value={!r}, degree={!r}, representation={!r}'
              .format(self.__int__(), self.degree, PolyRepresentation.NORMAL)
        )

    def __getitem__(self, i):
        """Return the coefficient of the x^i term."""
        if not 0 <= i <= self.degree:
            raise IndexError('Invalid index for polynomial of degree {}: {}'
                             .format(self.degree, i))
        if i in [0, self.degree]:
            return 1
        else:
            return self._bits[i]

    def __str__(self):
        """Return the mathematical notation of the polynomial.

        >>> str(Polynomial(0x3, 4, PolyRepresentation.NORMAL))
        'x^4 + x + 1'
        >>> str(Polynomial(0xC, 4, PolyRepresentation.REVERSED))
        'x^4 + x + 1'
        >>> str(Polynomial(0x9, 4, PolyRepresentation.KOOPMAN))
        'x^4 + x + 1'
        """
        def format_term(i):
            if i == 0: return '1'
            elif i == 1: return 'x'
            else: return 'x^{}'.format(i)

        return ' + '.join(format_term(i)
                          for i in reversed(range(len(self))) if self[i])


def crc(data, poly, init=None):
    """Calculate the CRC value of the data using the given polynomial.

    >>> p = Polynomial(value=0x62cc, degree=15)  # known as CRC-15-CAN
    >>> '{:04x}'.format(int(crc(data=Bits(value=0x00384c0, size=25), poly=p)))
    '007c'
    """
    reg_size = poly.degree
    poly = poly._bits

    if init is None:
        reg = Bits.all_ones(reg_size)
    else:
        reg = Bits(value=int(init), size=reg_size)

    for data_bit in reversed(data):  # MSB to LSB == left to right
        high_bit = int(reg.popleft()) ^ data_bit
        reg.append(0)
        if high_bit:
            reg ^= poly

    return reg

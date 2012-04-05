def int2bitstring(x, n=None):
    if n is not None:
        x += 2**n # support two's complement (must specify n)
    s = bin(x)[2:] # remove '0b' at the beginning of the resulting string
    # if desired make string of length n: pad if shorter, cut if longer
    if n is not None:
        s = s.rjust(n, '0')[-n:]
    return s
    # reverse: s = int2bitstring(x)
    #      --> x = int(s, 2)

def int2bytelist(x, n=4):
    return [(x >> (8*i)) % 0x100 for i in range(n)]
    # reverse: b = int2bytelist(x, n)
    #      --> x = sum(bi << (8*i) for (i, bi) in enumerate(b)


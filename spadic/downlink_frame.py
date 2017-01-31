from stsxyter_frame import DownlinkFrame

# request types
WRaddr = 1
WRdata = 2

def write_register_words(chip_address, reg_address, value):
    """Return the two frames required for writing a value to a register,
    as a flat lists of bytes.

    >>> ['{:02x}'.format(w) for w in write_register_words(7, 12, 367)]
    ['70', '40', '06', '7d', 'e9', '71', '80', 'b7', 'f7', 'b9']
    """
    # Any two consecutive sequence numbers will be accepted by SPADIC 2.0.
    return b''.join(
        bytes(DownlinkFrame(chip_address, seq, request, payload))
        for seq, request, payload in [
           (0,   WRaddr,  reg_address),
           (1,   WRdata,  value)
        ]
    )

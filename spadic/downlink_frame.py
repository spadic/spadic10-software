from stsxyter_frame import DownlinkFrame, RequestType

def write_register_words(chip_address, reg_address, value):
    """Return the two frames required for writing a value to a register,
    as a flat lists of bytes.

    >>> ['{:02x}'.format(w) for w in write_register_words(7, 12, 367)]
    ['70', '40', '06', '7d', 'e9', '71', '80', 'b7', 'f7', 'b9']
    """
    # Any two consecutive sequence numbers will be accepted by SPADIC 2.0.
    return b''.join(
        bytes(DownlinkFrame(chip_address, seq, request, payload))
        for seq, request,             payload in [
           (0,   RequestType.WR_ADDR, reg_address),
           (1,   RequestType.WR_DATA, value)
        ]
    )

def write_registers(ftdi, chip_address, operations):
    """Given an Ftdi instance, send bytes to write registers."""
    for reg_address, value in operations:
        ftdi.write(write_register_words(chip_address, reg_address, value))

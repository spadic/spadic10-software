from stsxyter_frame import DownlinkFrame, RequestType

def write_registers(ftdi, chip_address, operations):
    """Given an Ftdi instance, send bytes to write registers."""
    def write_register_frames(chip_address, reg_address, value):
        # Any two consecutive sequence numbers will be accepted by SPADIC 2.0.
        for seq, request,             payload in [
           (0,   RequestType.WR_ADDR, reg_address),
           (1,   RequestType.WR_DATA, value)
        ]:
            yield DownlinkFrame(chip_address, seq, request, payload)

    for reg_address, value in operations:
        for frame in write_register_frames(chip_address, reg_address, value):
            ftdi.write(bytes(frame))

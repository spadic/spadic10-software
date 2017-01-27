from .stsxyter_frame import DownlinkFrame, RequestType

class SpadicStsxyterRegisterAccess:
    """Read and write SPADIC registers using the STS-XYTER interface."""

    def __init__(self, stsxyter, chip_address):
        self._stsxyter = stsxyter
        self._chip_address = chip_address

    def write_registers(self, operations):
        """Perform register write operations as specified in the given list of
        (address, value) tuples.
        """
        def write_register_frames(reg_address, value):
            # Any two consecutive sequence numbers will be accepted by SPADIC 2.0.
            for seq, request,             payload in [
               (0,   RequestType.WR_ADDR, reg_address),
               (1,   RequestType.WR_DATA, value)
            ]:
                yield DownlinkFrame(self._chip_address, seq, request, payload)

        for reg_address, value in operations:
            for frame in write_register_frames(reg_address, value):
                self._stsxyter.write(frame)

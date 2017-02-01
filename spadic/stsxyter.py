from itertools import cycle

from .stsxyter_frame import DownlinkFrame, RequestType

class SpadicStsxyterRegisterAccess:
    """Read and write SPADIC registers using the STS-XYTER interface."""

    def __init__(self, stsxyter, chip_address):
        self._stsxyter = stsxyter
        self._chip_address = chip_address
        def sequence_number_count():
            size = DownlinkFrame._fields['sequence_number']
            return 2 ** size
        self._sequence_numbers = cycle(range(sequence_number_count()))

    def write_registers(self, operations):
        """Perform register write operations as specified in the given list of
        (address, value) tuples.
        """
        def write_register_frames(reg_address, value):
            for request, payload in [
                (RequestType.WR_ADDR, reg_address),
                (RequestType.WR_DATA, value)
            ]:
                yield DownlinkFrame(
                    self._chip_address, next(self._sequence_numbers),
                    request, payload
                )

        for reg_address, value in operations:
            for frame in write_register_frames(reg_address, value):
                self._stsxyter.write(frame)

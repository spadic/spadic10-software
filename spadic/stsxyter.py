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

        def all_frames(operations):
            for reg_address, value in operations:
                for frame in write_register_frames(reg_address, value):
                    yield frame

        # Send and remember all write requests.
        requests = list(all_frames(operations))
        for r in requests:
            self._stsxyter.write(r)

        # Collect all Ack frames available, waiting as short as possible for
        # the last one.
        acks = iter(lambda: self._stsxyter.read_ack(timeout=0.01), None)

        # TODO check CRC errors and if acks match requests

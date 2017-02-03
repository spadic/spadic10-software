from itertools import cycle
import logging

from .sequence_alignment import align_local
from .registerfile import RegisterReadFailure
from .stsxyter_frame import AckType, DownlinkFrame, RequestType, UplinkReadData

class SpadicStsxyterRegisterAccess:
    """Read and write SPADIC registers using the STS-XYTER interface."""

    def __init__(self, stsxyter, chip_address):
        self._stsxyter = stsxyter
        self._chip_address = chip_address
        def sequence_number_count():
            size = DownlinkFrame._fields['sequence_number']
            return 2 ** size
        self._sequence_numbers = cycle(range(sequence_number_count()))
        self._log = logging.getLogger(type(self).__name__)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

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

    def read_registers(self, addresses, attempt_alignment=True):
        """Generate register read results corresponding to a list of addresses.

        If the sequence numbers in read requests and responses do not
        correspond exactly, attempt to align them. Unmatched read requests will
        result in a read value of None.

        If it is required that all read requests are successfully handled on
        the first try, the alignment attempt can be disabled. In this case,
        a RegisterReadFailure exception is raised.
        """

        # Send and remember all read requests.
        def read_register_frame(register_address):
            return DownlinkFrame(
                self._chip_address, next(self._sequence_numbers),
                RequestType.RD_DATA, register_address
            )

        requests = [read_register_frame(a) for a in addresses]

        # TODO limit number of pending responses - to 8? to 1?
        for r in requests:
            self._stsxyter.write(r)

        def expected_sequence_number(request):
            """Return the sequence number expected in the response
            corresponding to the request."""
            size = UplinkReadData._fields['sequence_number']
            return int(request.sequence_number) % (2 ** size)

        expected_sequence_numbers = [
            expected_sequence_number(r) for r in requests
        ]

        # Try to read as many responses as requests were sent (with a short
        # timeout).
        responses = list(filter(None,
            (self._stsxyter.read_reg_data(timeout=None) for _ in requests)
        ))

        # Hope for the easily handled correct case.
        def returned_sequence_number(response):
            """Return the sequence number found in the response, or None if
            the CRC of the response is incorrect."""
            return (int(response.sequence_number)
                    if response.crc_is_correct else None)

        returned_sequence_numbers = [
            returned_sequence_number(r) for r in responses
        ]

        def read_results_simple(responses):
            """Generate register read values from responses."""
            for response in responses:
                yield int(response.data)

        if returned_sequence_numbers == expected_sequence_numbers:
            return read_results_simple(responses)

        # There could be several reasons why the results are not correct:
        #
        # a) Excessive RDdata frames (maybe misidentified other frames)
        # b) Missing RDdata frames (maybe due to CRC error in request)
        # c) RDdata frames with wrong sequence numbers and/or CRC errors
        #
        # To resolve cases a) and b), try to read all remaining RDdata frames
        # that are available within a small timeout (for a) this "cleans up"
        # for future register read operations, for b) maybe the missing
        # responses are received).
        #
        # Additionally read all Ack frames (which are sent with ack code "not
        # acknowledged") when a register read operation failed due to CRC error
        # in the request) available within a small timeout, to "clean up" for
        # future register write operations.
        responses.extend(
            iter(lambda: self._stsxyter.read_reg_data(timeout=0.1), None)
        )
        all_acks = iter(lambda: self._stsxyter.read_ack(timeout=0.1), None)
        nacks = [a for a in all_acks if int(a.ack) == AckType.NACK]

        # Hope again for the simple and correct case.
        returned_sequence_numbers = [
            returned_sequence_number(r) for r in responses
        ]

        if returned_sequence_numbers == expected_sequence_numbers:
            return read_results_simple(responses)

        # Attempt to align the received responses with the requests, or give up
        # and raise an exception.
        if not attempt_alignment:
            raise RegisterReadFailure

        alignment = dict(align_local(
            expected_sequence_numbers, returned_sequence_numbers
        ))

        def read_values_aligned(requests, responses, alignment):
            """Generate register read results from aligned requests and
            responses. Use None as value if there is no matching response to
            a request."""
            for i, _ in enumerate(requests):
                j = alignment.get(i, None)
                reg_value = None if j is None else int(responses[j].data)
                yield reg_value

        self._log.info('Matched {} responses to {}/{} requests. '
                       'Received {} NACKs.'
                       .format(len(responses), len(alignment), len(requests),
                               len(nacks)))

        return read_values_aligned(requests, responses, alignment)

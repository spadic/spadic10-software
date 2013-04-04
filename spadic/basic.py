import signal

import ftdi_cbmnet
from bit_byte_helper import int2bitstring, int2bytelist


#====================================================================
# prepare timeout
#====================================================================
class TimeoutException(Exception):
    pass

# set timeout handler for SIGALRM to raise TimeoutException
def timeout_handler(signum, frame):
    raise TimeoutException()
signal.signal(signal.SIGALRM, timeout_handler)


#====================================================================
# constants
#====================================================================

#--------------------------------------------------------------------
# CBMnet <-> Register file read/write commands
#--------------------------------------------------------------------
RF_WRITE = 1
RF_READ = 2

# size of package parts in IOM package mode
# first byte is always 0xFF --> discard after read
PACKAGE_SIZE = 9


#====================================================================
# FTDI -> IO Manager -> SPADIC communication
#====================================================================

class Spadic(ftdi_cbmnet.FtdiCbmnet):
    """SPADIC communication via FTDI -> CBMnet interface."""
    _debug = False
    _dummy = False
    #----------------------------------------------------------------
    # register file access
    #----------------------------------------------------------------
    def write_register(self, address, data):
        if self._debug:
            print 'RF[0x%03X] = 0x%04X' % (address, data)
        self._cbmif_write([RF_WRITE, address, data])

    def read_register(self, address):
        # write register address
        self._cbmif_write([RF_READ, address, 0])
        # read register value
        (src, data) = self._cbmif_read()
        return data

    #----------------------------------------------------------------
    # read data from test output -> IOM -> FTDI
    # (assuming package mode is used)
    #----------------------------------------------------------------
    def read_data(self, num_bytes=None, timeout=1):
        # read data until num_bytes are read (None -> 'infinity')
        # abort if timeout is over after no data was received
        num_bytes_left = num_bytes
        while num_bytes is None or num_bytes_left >= PACKAGE_SIZE:
            if timeout is not None:
                signal.alarm(timeout) # set alarm
            try:
                bytes_read = self._ftdi_read(PACKAGE_SIZE)[1:]
                             # discard the first byte
            except TimeoutException:
                break
            finally:
                signal.alarm(0) # disable alarm in any case

            for byte in bytes_read:
                yield byte
            if num_bytes_left:
                num_bytes_left -= len(bytes_read)


class SpadicDummy:
    """Fake the Spadic interface to test without USB connection."""
    _debug = False
    _dummy = True
    def write_register(self, address, data):
        if self._debug:
            print 'RF[0x%03X] = 0x%04X' % (address, data)
    def read_register(self, address):
        return 0
    def read_data(self, num_bytes=None, timeout=1):
        for byte in []:
            yield byte
            

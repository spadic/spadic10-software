import ftdi
# http://www.intra2net.com/en/developer/libftdi/documentation/group__libftdi.html


#====================================================================
# constants
#====================================================================

#--------------------------------------------------------------------
# dictionary of known USB error codes
#--------------------------------------------------------------------
USB_ERROR_CODE = {
   -16: 'device busy',
  -110: 'timeout',
  -666: 'device unavailable'
}

#--------------------------------------------------------------------
# IO Manager commands
#--------------------------------------------------------------------
IOM_WR = 0x01 # write
IOM_RD = 0x02 # read


#====================================================================
# FTDI -> IO Manager communication base class
#====================================================================

class FtdiIom:
    #----------------------------------------------------------------
    # open/close USB connection with constructor/destructor methods
    #----------------------------------------------------------------
    def __init__(self, VID=0x0403, PID=0x6010):
        context = ftdi.ftdi_new()
        if not (ftdi.ftdi_usb_open(context, VID, PID) == 0):
            ftdi.ftdi_free(context)
            self.ftdic = None
            raise IOError('could not open USB connection!')
        ftdi.ftdi_set_bitmode(context, 0, ftdi.BITMODE_SYNCFF)
        self.ftdic = context

    def __del__(self):
        if self.ftdic is not None:
            ftdi.ftdi_usb_close(self.ftdic)
            ftdi.ftdi_free(self.ftdic)

    #----------------------------------------------------------------
    # reset FTDI, or reconnect entirely
    #----------------------------------------------------------------
    def reset(self):
        if self.ftdic is not None:
            ftdi.ftdi_usb_reset(self.ftdic)

    def reconnect(self):
        self.__del__()
        self.__init__()

    #----------------------------------------------------------------
    # FTDI communication
    #----------------------------------------------------------------
    def _ftdi_write(self, byte_list, max_iter=None):
        bytes_left = byte_list
        iter_left = max_iter
        while bytes_left:
            if iter_left == 0:
                break
            n = ftdi.ftdi_write_data(self.ftdic,
                    ''.join(map(chr, bytes_left)), len(bytes_left))
            if n < 0:
                raise IOError('USB write error (error code %i: %s)'
                              % (n, USB_ERROR_CODE[n]
                                    if n in USB_ERROR_CODE else 'unknown'))
            bytes_left = bytes_left[n:]
            if iter_left is not None:
                iter_left -= 1
        # number of bytes that were written
        return len(byte_list)-len(bytes_left)

    def _ftdi_read(self, num_bytes, max_iter=None):
        buf = chr(0)*num_bytes
        bytes_read = []
        iter_left = max_iter
        while buf:
            if iter_left == 0:
                break
            n = ftdi.ftdi_read_data(self.ftdic, buf, len(buf))
            if n < 0:
                raise IOError('USB read error (error code %i: %s)'
                              % (n, USB_ERROR_CODE[n]
                                    if n in USB_ERROR_CODE else 'unknown'))
            bytes_read += map(ord, buf[:n])
            buf = buf[n:]
            if iter_left is not None:
                iter_left -= 1
        return bytes_read

    #----------------------------------------------------------------
    # IO Manager communication
    #----------------------------------------------------------------
    def _iom_write(self, iom_addr, iom_payload, max_iter=None):
        iom_len = len(iom_payload)
        iom_header = [IOM_WR, iom_addr, iom_len]
        num_written = self._ftdi_write(iom_header + iom_payload, max_iter)
        return num_written

    def _iom_read(self, iom_addr, num_bytes, max_iter=None):
        # only suitable if package mode is not used
        num_bytes_written = self._ftdi_write([IOM_RD, iom_addr, num_bytes],
                                              max_iter)
        if not num_bytes_written == num_bytes:
            raise IOError('%i bytes were not written!' %
                          (num_bytes-num_bytes_written))
        # read [iom_addr, num_data, data]
        iom_data = self._ftdi_read(2+num_bytes, max_iter)
        iom_addr_ret = iom_data[0]
        iom_num_bytes = iom_data[1]
        iom_payload = iom_data[2:]
        if not (iom_addr_ret == iom_addr):
            raise ValueError('wrong IO Manager address! '
                             '(expected: 0x%02X found: 0x%02X)' %
                              (iom_addr, iom_addr_ret))
        if not (iom_num_bytes == len(iom_payload)):
            raise ValueError('wrong number of bytes indicated! '
                             '(indicated: %i found: %i)' %
                              (iom_num_bytes, len(iom_payload)))
        if not (iom_num_bytes == num_bytes):
            raise ValueError('wrong number of bytes read! '
                             '(expected: %i found: %i)' %
                              (num_bytes, iom_num_bytes))
        # if all tests are passed, len(iom_payload) == num_bytes
        return iom_payload


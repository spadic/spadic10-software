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
# FTDI -> CBMnet interface communication base class
#====================================================================

class FtdiCbmnet:
    #----------------------------------------------------------------
    # open/close USB connection with constructor/destructor
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
            ftdi.ftdi_set_bitmode(self.ftdic, 0, ftdi.BITMODE_RESET)
            ftdi.ftdi_free(self.ftdic)
                    # free -> deinit -> usb_close_internal -> usb_close

    def purge(self):
        """Purge all FTDI buffers."""
        if self.ftdic is not None:
            ftdi.ftdi_usb_purge_buffers(self.ftdic)
        
    def reset(self):
        """Reset the FTDI chip."""
        if self.ftdic is not None:
            ftdi.ftdi_usb_reset(self.ftdic)

    def reconnect(self):
        """Close and re-open FTDI connection.
        
        Sets the FTDI bitmode to BITMODE_RESET before disconnecting, and
        back to BITMODE_SYNCFF after reconnecting. This disables the FTDI
        output clock during this period.
        """
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
    # CBMnet interface communication
    #----------------------------------------------------------------
    def _cbmif_write(self, data, max_iter=None):
        # TODO when firmware is adapted, use mux address & num_data
        ftdi_data = []
        # split 16-bit values into two 8-bit values
        for d in data:
            ftdi_data.append(d//0x100)
            ftdi_data.append(d%0x100)
        num_written = self._ftdi_write(ftdi_data, max_iter)
        return num_written

    def _cbmif_read(self, max_iter=None):
        [src, num_data] = self._ftdi_read(2, max_iter)
        data = self._ftdi_read(2*num_data, max_iter)
        # combine two 8-bit values to 16-bit values
        return (src, [(data[2*i]<<8) + (data[2*i+1]) for i in range(num_data)])


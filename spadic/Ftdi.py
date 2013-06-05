import ftdi
# http://www.intra2net.com/en/developer/libftdi/documentation/group__libftdi.html


#--------------------------------------------------------------------
# dictionary of known USB error codes
#--------------------------------------------------------------------
USB_ERROR_CODE = {
   -16: 'device busy',
  -110: 'timeout',
  -666: 'device unavailable'
}


#====================================================================
# FTDI communication wrapper
#====================================================================
class Ftdi:
    """Wrapper for simple FTDI communication."""

    #----------------------------------------------------------------
    # connection management methods
    #----------------------------------------------------------------
    def __init__(self, VID=0x0403, PID=0x6010):
        """Open USB connection and initialize FTDI context."""
        context = ftdi.ftdi_new()
        if not (ftdi.ftdi_usb_open(context, VID, PID) == 0):
            ftdi.ftdi_free(context)
            self.ftdic = None
            raise IOError('could not open USB connection!')
        ftdi.ftdi_set_bitmode(context, 0, ftdi.BITMODE_SYNCFF)
        self.ftdic = context
        self._debug_ftdi = False
        self._debug_out = None

    def _debug(self, *text):
        try:
            print >> self._debug_out, " ".join(map(str, text))
            self._debug_out.flush()
        except:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        """Deinitialize FTDI context and close USB connection."""
        if self.ftdic is not None:
            #ftdi.ftdi_set_bitmode(self.ftdic, 0, ftdi.BITMODE_RESET)
            ftdi.ftdi_free(self.ftdic)
                    # free -> deinit -> usb_close_internal -> usb_close
        if self._debug_ftdi:
            self._debug("FTDI exit")

    def purge(self):
        """Purge all FTDI buffers."""
        if self.ftdic is not None:
            ftdi.ftdi_usb_purge_buffers(self.ftdic)
        
    def reset(self):
        """Reset the FTDI chip."""
        if self.ftdic is not None:
            ftdi.ftdi_usb_reset(self.ftdic)

    def reconnect(self):
        """Close and re-open FTDI connection."""
        self.__exit__()
        self.__init__()

    #----------------------------------------------------------------
    # data transfer methods
    #----------------------------------------------------------------
    def _ftdi_write(self, byte_list, max_iter=None):
        """Write data to the FTDI chip."""
        if self._debug_ftdi:
            self._debug_("FTDI write [" +
                " ".join("%02X" % b for b in byte_list) + "]")
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
        """Read data from the FTDI chip."""
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
        if self._debug_ftdi and bytes_read:
            self._debug("FTDI  read [" +
                " ".join("%02X" % b for b in bytes_read) + "]")
        return bytes_read


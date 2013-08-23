import threading

try:
    # libFTDI was renamed when version 1.0 was released -- try to get the
    # newer version first.
    import ftdi1 as ftdi
except ImportError:
    import ftdi
    # Since libFTDI v0.20, the method names have changed:
    # The file libftdi/python/ftdi1.i now contains the line
    # %rename("%(strip:[ftdi_])s") "";
    # If we have the older version of libFTDI, we change the method names
    # now, so we are compatible with v1.0:
    for name in dir(ftdi):
        if name.startswith('ftdi_'):
            newname = name[len('ftdi_'):]
            setattr(ftdi, newname, getattr(ftdi, name))


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

# libFTDI documentation:
# http://www.intra2net.com/en/developer/libftdi/documentation/group__libftdi.html

class Ftdi:
    """Wrapper for simple FTDI communication."""

    #----------------------------------------------------------------
    # connection management methods
    #----------------------------------------------------------------
    def __init__(self, VID=0x0403, PID=0x6010, _debug_out=None):
        """Open USB connection and initialize FTDI context."""
        context = ftdi.new()
        if not (ftdi.usb_open(context, VID, PID) == 0):
            ftdi.free(context)
            self.ftdic = None
            raise IOError('could not open USB connection!')
        ftdi.set_bitmode(context, 0, ftdi.BITMODE_SYNCFF)
        self.ftdic = context
        self._debug_ftdi = False
        self._debug_out = _debug_out
        self._debug_lock = threading.Lock()

        # how to get and set the write buffer chunk size:

        # libFTDI <1.0:
        #chunksize_p = ftdi.new_uintp()
        #ftdi.write_data_get_chunksize(context, chunksize_p)
        #chunksize = ftdi.uintp_value(chunksize_p))
        #ftdi.write_data_set_chunksize(context, chunksize)
        # libFTDI 1.0:
        #chunksize = ftdi.write_data_get_chunksize(context)[1]
        #ftdi.write_data_set_chunksize(context, chunksize)

    def _debug(self, *text):
        with self._debug_lock:
            try:
                print >> self._debug_out, " ".join(map(str, text))
                self._debug_out.flush()
            except:
                pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        """Deinitialize FTDI context and close USB connection."""
        self.purge()
        self.reset()
        if self.ftdic is not None:
            #ftdi.set_bitmode(self.ftdic, 0, ftdi.BITMODE_RESET)
            ftdi.free(self.ftdic)
                    # free -> deinit -> usb_close_internal -> usb_close
        if self._debug_ftdi:
            self._debug("[FTDI] exit")

    def purge(self):
        """Purge all FTDI buffers."""
        if self.ftdic is not None:
            ftdi.usb_purge_buffers(self.ftdic)
        
    def reset(self):
        """Reset the FTDI chip."""
        if self.ftdic is not None:
            ftdi.usb_reset(self.ftdic)

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
            self._debug("[FTDI] write",
                        "[%s]"%(" ".join("%02X" % b for b in byte_list)))
        bytes_left = byte_list
        iter_left = max_iter
        while bytes_left:
            if iter_left == 0:
                break
            n = ftdi.write_data(self.ftdic,
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
            n = ftdi.read_data(self.ftdic, buf, len(buf))
            if n < 0:
                raise IOError('USB read error (error code %i: %s)'
                              % (n, USB_ERROR_CODE[n]
                                    if n in USB_ERROR_CODE else 'unknown'))
            bytes_read += map(ord, buf[:n])
            buf = buf[n:]
            if iter_left is not None:
                iter_left -= 1
        if self._debug_ftdi and bytes_read:
            self._debug("[FTDI] read",
                        "[%s]"%(" ".join("%02X" % b for b in bytes_read)))
        return bytes_read


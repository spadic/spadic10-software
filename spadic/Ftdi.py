import threading

# libFTDI was renamed when version 1.0 was released -- try to get the
# newer version first.
try:
    import ftdi1 as ftdi
    LIBFTDI_OLD = False
except ImportError:
    import ftdi
    LIBFTDI_OLD = True

# We write our code as if we had libFTDI v1.0 -- if not, we have to make
# it compatible.

# Since libFTDI v0.20, the method names have changed:
# v0.x: ftdi.ftdi_[...]
# v1.0: ftdi.[...]
#
# This comes from the following line in the file libftdi/python/ftdi1.i:
#
#   %rename("%(strip:[ftdi_])s") "";
#
# If we have the older version of libFTDI, we need to change the method
# names here:
if LIBFTDI_OLD:
    for name in dir(ftdi):
        if name.startswith('ftdi_'):
            newname = name[len('ftdi_'):]
            setattr(ftdi, newname, getattr(ftdi, name))

# Next, we have to account for improved behaviour of some methods:
#
# v0.x: read_data(context, *buf, size) -> code
# v1.0: read_data(context, size) -> [code, buf]
#
# This change comes from the following code in ftdi1.i:
#
#  %typemap(in,numinputs=1) (unsigned char *buf, int size) %{ $2 = PyInt_AsLong($input);$1 = (unsigned char*)malloc($2*sizeof(char)); %}
#  %typemap(argout) (unsigned char *buf, int size) %{ if(result<0) $2=0; $result = SWIG_Python_AppendOutput($result, convertString((char*)$1, $2)); free($1); %}
#      int ftdi_read_data(struct ftdi_context *ftdi, unsigned char *buf, int size);
#  %clear (unsigned char *buf, int size);
#
# If we have the older version, we have to redefine the method:
if LIBFTDI_OLD:
    def read_data(context, size):
        buf = '\x00'*size
        code = ftdi.ftdi_read_data(context, buf, size)
        result = '' if code < 0 else buf
        return [code, result]
    # here we are lucky that the names have changed...
    ftdi.read_data = read_data

# There are other methods that have changed, but are not needed here,
# for example:
#
# v0.x: 
#   chunksize_p = ftdi.new_uintp()
#   ftdi.write_data_get_chunksize(context, chunksize_p)
# v1.0:
#   chunksize = ftdi.write_data_get_chunksize(context)[1]
#
# v0.x: 
#   chunksize = ftdi.uintp_value(chunksize_p))
#   ftdi.write_data_set_chunksize(context, chunksize)
# v1.0:
#   ftdi.write_data_set_chunksize(context, chunksize)
#
# For more details, get the libFTDI source code and consult python/ftdi1.i


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
        bytes_left = num_bytes
        bytes_read = []
        iter_left = max_iter
        while bytes_left:
            if iter_left == 0:
                break
            [n, buf] = ftdi.read_data(self.ftdic, bytes_left)
            if n < 0:
                raise IOError('USB read error (error code %i: %s)'
                              % (n, USB_ERROR_CODE[n]
                                    if n in USB_ERROR_CODE else 'unknown'))
            bytes_read += map(ord, buf[:n])
            bytes_left -= n
            if iter_left is not None:
                iter_left -= 1
        if self._debug_ftdi and bytes_read:
            self._debug("[FTDI] read",
                        "[%s]"%(" ".join("%02X" % b for b in bytes_read)))
        return bytes_read


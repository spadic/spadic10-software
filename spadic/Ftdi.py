"""Provides a simplified interface for the most commonly used functions of the
libFTDI Python bindings.
"""

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

    from util import log as _log
    def _debug(self, *text):
        self._log.debug(' '.join(text))

    #----------------------------------------------------------------
    # connection management methods
    #----------------------------------------------------------------
    def __init__(self, VID=0x0403, PID=0x6010):
        """Prepare, but don't initialize FTDI context."""
        self._VID = VID
        self._PID = PID
        self._context = None
        self._debug("init")

    def __enter__(self):
        """Open USB connection and initialize FTDI context."""
        context = ftdi.new()
        if not ftdi.usb_open(context, self._VID, self._PID) == 0:
            ftdi.free(context)
            raise IOError('Could not open USB connection.')
        if not ftdi.set_bitmode(context, 0, ftdi.BITMODE_SYNCFF) == 0:
            ftdi.free(context)
            raise IOError('Could not set FTDI synchronous FIFO mode.')
        self._context = context
        self._debug("enter")
        return self

    def __exit__(self, *args):
        """Deinitialize FTDI context and close USB connection."""
        self.purge()
        self.reset()
        if self._context:
            ftdi.free(self._context)
            # free -> deinit -> usb_close_internal -> usb_close
        self._debug("exit")

    def purge(self):
        """Purge all FTDI buffers."""
        if not self._context:
            raise RuntimeError('FTDI context not initialized.')
        ftdi.usb_purge_buffers(self._context)

    def reset(self):
        """Reset the FTDI chip."""
        if not self._context:
            raise RuntimeError('FTDI context not initialized.')
        ftdi.usb_reset(self._context)

    def reconnect(self):
        """Close and re-open FTDI connection."""
        self.__exit__()
        self.__enter__()

    #----------------------------------------------------------------
    # data transfer methods
    #----------------------------------------------------------------
    def write(self, byte_str, max_iter=None):
        """
        Write a sequence of bytes (encoded as a string) to the FTDI chip.

        `max_iter`: Maximum number of retries, should not all the data
            be written at once. `None` means unlimited retries.

        Returns the number of bytes written (can be less than the length
        of `byte_str`).
        """
        if not self._context:
            raise RuntimeError('FTDI context not initialized.')

        self._debug("write",
                    "[%s]"%(" ".join("%02X" % ord(b) for b in byte_str)))
        bytes_left = byte_str
        iter_left = max_iter
        while bytes_left:
            if iter_left == 0:
                break
            n = ftdi.write_data(self._context, bytes_left, len(bytes_left))
            if n < 0:
                raise IOError('USB write error (error code %i: %s)'
                              % (n, USB_ERROR_CODE[n]
                                    if n in USB_ERROR_CODE else 'unknown'))
            bytes_left = bytes_left[n:]
            if iter_left is not None:
                iter_left -= 1
        # number of bytes that were written
        return len(byte_str) - len(bytes_left)

    def read(self, num_bytes, max_iter=None):
        """
        Read a sequence of bytes (encoded as a string) from the FTDI chip.

        `num_bytes`: Requested number of bytes to read.
        `max_iter`: Maximum number of retries, should the requested
            number of bytes not be available at once. `None` means
            unlimited retries.

        Returns the read bytes encoded as a string (can be fewer than
        `num_bytes`).
        """
        if not self._context:
            raise RuntimeError('FTDI context not initialized.')

        bytes_left = num_bytes
        bytes_read = ''
        iter_left = max_iter
        while bytes_left:
            if iter_left == 0:
                break
            n, buf = ftdi.read_data(self._context, bytes_left)
            if n < 0:
                raise IOError('USB read error (error code %i: %s)'
                              % (n, USB_ERROR_CODE[n]
                                    if n in USB_ERROR_CODE else 'unknown'))
            bytes_read += buf[:n]
            bytes_left -= n
            if iter_left is not None:
                iter_left -= 1
        if bytes_read:
            self._debug("read",
                        "[%s]"%(" ".join("%02X" % ord(b) for b in bytes_read)))
        return bytes_read

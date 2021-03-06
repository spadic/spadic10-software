"""Provides a simplified interface for the most commonly used functions of the
libFTDI Python bindings.
"""

from functools import wraps
import logging

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
        buf = b'\x00' * size
        code = ftdi.ftdi_read_data(context, buf, size)
        result = b'' if code < 0 else buf
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

    from .util import log as _log
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
        self._debug('init')

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
        self._debug('enter')
        return self

    def __exit__(self, *args):
        """Deinitialize FTDI context and close USB connection."""
        self.purge()
        self.reset()
        if self._context:
            ftdi.free(self._context)
            # free -> deinit -> usb_close_internal -> usb_close
        self._debug('exit')

    def _require_context(function):
        @wraps(function)
        def function_with_context(self, *args, **kwargs):
            if not self._context:
                raise RuntimeError('FTDI context not initialized.')
            return function(self, *args, **kwargs)
        return function_with_context

    @_require_context
    def purge(self):
        """Purge all FTDI buffers."""
        ftdi.usb_purge_buffers(self._context)

    @_require_context
    def reset(self):
        """Reset the FTDI chip."""
        ftdi.usb_reset(self._context)

    def reconnect(self):
        """Close and re-open FTDI connection."""
        self.__exit__()
        self.__enter__()

    #----------------------------------------------------------------
    # data transfer methods
    #----------------------------------------------------------------
    @_require_context
    def write(self, data, max_iter=None):
        """Write data (a bytes object) to the FTDI chip.

        `max_iter`: Maximum number of retries, should not all the data
            be written at once. `None` means unlimited retries.

        Return the number of bytes written (can be less than the length
        of `data`).
        """
        self._debug('write',
                    '[%s]' % (' '.join('%02X' % byte for byte in data)))
        bytes_left = data
        iter_left = max_iter
        while bytes_left:
            if iter_left == 0:
                break
            n = ftdi.write_data(self._context, bytes_left)
            if n < 0:
                raise IOError('USB write error (error code %i: %s)'
                              % (n, USB_ERROR_CODE.get(n, 'unknown')))
            bytes_left = bytes_left[n:]
            if iter_left is not None:
                iter_left -= 1
        # number of bytes that were written
        return len(data) - len(bytes_left)

    @_require_context
    def read(self, num_bytes, max_iter=None):
        """Read data from the FTDI chip.

        `num_bytes`: Requested number of bytes to read.
        `max_iter`: Maximum number of retries, should the requested
            number of bytes not be available at once. `None` means
            unlimited retries.

        Return a bytes object (its length can be less than `num_bytes`).
        """
        bytes_left = num_bytes
        bytes_read = b''
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
            self._debug('read',
                        '[%s]' % (' '.join('%02X' % b for b in bytes_read)))
        return bytes_read


class FtdiContainer:
    """Use as a base class if a derived class should contain an Ftdi instance,
    rather than being a subclass of Ftdi itself.
    """
    def _debug(self, *text):
        _log = logging.getLogger(type(self).__name__)
        _log.info(' '.join(text)) # TODO use proper log levels

    def __init__(self, ftdi, *args, **kwargs):
        """Prepare FTDI connection."""
        self._ftdi = ftdi
        self._debug('init')
        super().__init__(*args, **kwargs)

    def __enter__(self):
        """Open FTDI connection."""
        self._ftdi.__enter__()
        self._debug('enter')

    def __exit__(self, *args):
        """Close FTDI connection."""
        self._ftdi.__exit__(*args)
        self._debug('exit')

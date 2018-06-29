__all__ = []

# Move the Spadic class from its module namespace to the top-level spadic
# package namespace (i.e., here). If libFTDI is not installed, this will fail.
try:
    from .main import Spadic
    del main
    __all__ += ['Spadic']
except ImportError:
    raise ImportError('Did you install libFTDI properly?')

__version__ = '1.1.8'

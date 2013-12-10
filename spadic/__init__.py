__all__ = []

# Try to move Spadic and SpadicServer from their module namespaces to the
# top-level spadic package namespace (i.e., here). If libFTDI is not
# installed, this will fail, but we allow the spadic package to be
# imported without them.
try:
    from main import Spadic
    from server import SpadicServer
    del main
    del server
    __all__ += ['Spadic', 'SpadicServer']
except ImportError:
    pass

# Move the clients from their module namespace to the top-level spadic
# package namespace. They don't need libFTDI and will be available in any
# case.
from client import SpadicControlClient, SpadicDataClient
del client
__all__ += ['SpadicControlClient', 'SpadicDataClient']

__version__ = '1.1.7'


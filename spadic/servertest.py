import sys

import server

with server.SpadicServerRF() as serv:
    try:
        serv.run()
    except KeyboardInterrupt:
        sys.exit('Quit.')


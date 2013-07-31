import sys

import main
import server

f = open('/tmp/spadic/spadic.log', 'w')
with main.Spadic(_debug_cbmif=1, _debug_out=f) as sp:
    rf = sp._registerfile
    with server.SpadicRFServer(rf) as serv:
        try:
            serv.start()
            serv.run()
        except KeyboardInterrupt:
            sys.exit('Quit.')


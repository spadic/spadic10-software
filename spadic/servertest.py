import sys
import time

import server

f = open('/tmp/spadic/spadic.log', 'w')
with server.SpadicServer(_debug_cbmif=1, _debug_server=1, _debug_out=f) as s:
    s._debug("started server")
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
    s._debug("interrupted server")


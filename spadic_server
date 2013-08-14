import sys
import time

import server

f = open('/tmp/spadic/server.log', 'w')
with server.SpadicServer(_debug_cbmif=1, _debug_ftdi=1,
                         _debug_server=1, _debug_out=f) as s:
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break


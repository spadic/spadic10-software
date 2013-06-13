#!/usr/bin/python

import sys
import spadic

reset = "--reset" in sys.argv
try:
    s = spadic.Spadic(reset, _debug_cbmif=1)
except:
    sys.exit(sys.exc_value)

s.ui_run()


#!/usr/bin/python

import sys
import spadic

#--------------------------------------------------------------------
# parse options
#--------------------------------------------------------------------
reset = "--reset" in sys.argv
full_error = "--full-error" in sys.argv

try:
    load_file = sys.argv[sys.argv.index("--load")+1]
except:
    load_file = None

#--------------------------------------------------------------------
# start spadic controller and user interface
#--------------------------------------------------------------------
try:
    s = spadic.Spadic(reset, load_file, _debug_cbmif=1)
    s.ui_run()
except:
    if full_error:
        raise
    else:
        sys.exit(sys.exc_value)


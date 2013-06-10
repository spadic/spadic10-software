import sys
import spadic

reset = "--reset" in sys.argv
s = spadic.Spadic(reset, _debug_cbmif=1)
s.control.ui.run()


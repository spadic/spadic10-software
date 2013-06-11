import sys
import spadic

reset = "--reset" in sys.argv
s = spadic.Spadic(reset, ui=1, _debug_cbmif=1)
s.control.ui.run()


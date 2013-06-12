import sys
import spadic

reset = "--reset" in sys.argv
f = open('spadic.log', 'w')
s = spadic.Spadic(reset, ui=1, _debug_cbmif=1, _debug_out=f)
s.control.ui.run()


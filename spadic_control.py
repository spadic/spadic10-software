#!/usr/bin/python

from spadic_control_lib import *


if __name__=='__main__':
    #if len(sys.argv < 3):
    #    sys.exit('usage: %s <reg_addr> <value>' % sys.argv[0])

    #address = int(sys.argv[1], 16)
    #value = int(sys.argv[2], 16)

    s = SpadicI2cRf()
    sr = SpadicShiftRegister()

    sr.set_value('dac1', 67)
    s.write_shiftregister(str(sr))

    # try to switch some LEDs on
    s.write_register(RF_MAP['overrides'], 0x20)


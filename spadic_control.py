#!/usr/bin/python

from spadic_control_lib import *


if __name__=='__main__':
    s = SpadicI2cRf()
    print 'opened USB connection.'

    # switch LED on
    s.write_register(RF_MAP['overrides'], 0x20)

    sr = SpadicShiftRegister()

    # sweep nCascN
    for v in [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120]:
        raw_input('Setting nCascN to %i. Press <Enter> to confirm.' % v)
        sr.set_value('nCascN', v)
        s.write_shiftregister(str(sr))

    # switch LED off
    s.write_register(RF_MAP['overrides'], 0x00)

    del s # not really necessary, should be done automatically
    print 'closed USB connection.'


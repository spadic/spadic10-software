#!/usr/bin/python

from spadic_control_lib import *
import time


if __name__=='__main__':
    s = Spadic()
    print 'opened USB connection.'

    # switch LED on
    s.write_register(RF_MAP['overrides'], 0x10)

    time.sleep(1)

    # switch LED off
    s.write_register(RF_MAP['overrides'], 0x00)

    del s # not really necessary, should be done automatically
    print 'closed USB connection.'


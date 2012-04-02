#!/usr/bin/python

from spadic_control_lib import *
import time

if __name__=='__main__':
    s = SpadicI2cRf()
    print 'opened USB connection.'

    # switch LED on
    s.write_register(RF_MAP['overrides'], 0x10)

    sr = SpadicShiftRegister()

    #sweep nCascN
    #for v in [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120]:
    #    raw_input('Setting nCascN to %i. Press <Enter> to confirm.' % v)
    #    sr.set_value('nCascN', v)
    #    s.write_register(RF_MAP['overrides'], 0x30)
    #    s.write_shiftregister(str(sr))
    #    s.write_register(RF_MAP['overrides'], 0x10)

    #ADC config
    #s.write_register(RF_MAP['REG_enableAdcDec_l'], 0x04)
 
    #ADC bias
    sr.set_value('VNDel', 61)    
    sr.set_value('VPDel', 61)          
    sr.set_value('VPLoadFB2', 61)
    sr.set_value('VPLoadFB', 61)
    sr.set_value('VPFB', 61)
    sr.set_value('VPAmp', 61)

    #channel config
    sr.set_value('baselineTrimN', 50)
    sr.set_value('SelMonitor', 1)  #1: CSA, 0: ADC
    sr.set_value('DecSelectNP', 1) #0: N, 1: P 

    #N channel bias 
    sr.set_value('nCascN', 30)
    sr.set_value('pCascN', 52)
    sr.set_value('nSourceBiasN', 50)
    sr.set_value('pSourceBiasN', 70)
    sr.set_value('pFBN', 60) 

    #P channel bias 
    sr.set_value('nCascP', 80)  #51                   #80
    sr.set_value('pCascP', 75)  #52                   #75
    sr.set_value('nSourceBiasP', 71) #51              #71
    sr.set_value('pSourceBiasP', 70) #55              #70
    sr.set_value('nFBP', 90) #50                      #90

    #P channel 0 config 
    sr.set_value('ampToBus_0', 0)
    sr.set_value('enMonitorAdc_0', 0)
    sr.set_value('frontEndSelNP_0', 0) #0: N, 1: P
    sr.set_value('enSignalAdc_0', 0)
    sr.set_value('enAmpN_0', 0) 
    sr.set_value('enAmpP_0', 0)
  
    #P channel 31 config -> trigger channel
    sr.set_value('ampToBus_31', 1)
    sr.set_value('enMonitorAdc_31', 0)
    sr.set_value('frontEndSelNP_31', 1) #0: N, 1: P
    sr.set_value('enSignalAdc_31', 1)
    sr.set_value('enAmpN_31', 0) 
    sr.set_value('enAmpP_31', 1)
    #s.write_register(RF_MAP['REG_enableAdcDec_h'], 0x10) #enable analog trigger
   
    #digital config
    s.write_register(RF_MAP['REG_enableTestOutput'], 1)
    s.write_register(RF_MAP['REG_enableTestInput'], 1)
    s.write_register(RF_MAP['REG_testOutputSelGroup'], 1) #select groupB
    s.write_register(RF_MAP['REG_disableChannelA'], 0)
    s.write_register(RF_MAP['REG_disableChannelB'], 0)
    s.write_register(RF_MAP['REG_disableEpochChannelA'], 1) 
    s.write_register(RF_MAP['REG_disableEpochChannelB'], 1) 

    #write values
    s.write_shiftregister(str(sr))

    # switch LED off
    s.write_register(RF_MAP['overrides'], 0x00)

    del s # not really necessary, should be done automatically
    print 'closed USB connection.'


#!/usr/bin/python

from spadic_registers import *


#====================================================================   
# dictionaries of default RF and SR configurations
# use these as arguments for Spadic.config()
#====================================================================   

#--------------------------------------------------------------------   
# shift register
#--------------------------------------------------------------------   

SR_DEFAULT = {
  # ADC bias
  'VNDel':     61,    
  'VPDel':     61,          
  'VPLoadFB2': 61,
  'VPLoadFB':  61,
  'VPFB':      61,
  'VPAmp':     61,
  
  # channel config
  'baselineTrimN': 50,
  'SelMonitor':     1, # 1: CSA, 0: ADC
  'DecSelectNP':    1, # 0: N, 1: P 
  
  # N channel bias 
  'nCascN':       30,
  'pCascN':       52,
  'nSourceBiasN': 50,
  'pSourceBiasN': 70,
  'pFBN':         60, 
  
  # P channel bias 
  'nCascP':       80, # 51  # 80
  'pCascP':       75, # 52  # 75
  'nSourceBiasP': 71, # 51  # 71
  'pSourceBiasP': 70, # 55  # 70
  'nFBP':         90, # 50  # 90
  
  # P channel 0 config 
  'ampToBus_0':      0,
  'enMonitorAdc_0':  0,
  'frontEndSelNP_0': 0, # 0: N, 1: P
  'enSignalAdc_0':   0,
  'enAmpN_0':        0, 
  'enAmpP_0':        0,
  
  # P channel 31 config -> trigger channel
  'ampToBus_31':      1,
  'enMonitorAdc_31':  0,
  'frontEndSelNP_31': 1, # 0: N, 1: P
  'enSignalAdc_31':   1,
  'enAmpN_31':        0, 
  'enAmpP_31':        1
}


#--------------------------------------------------------------------   
# register file
#--------------------------------------------------------------------   

RF_DEFAULT = {
  # ADC config
  #'REG_enableAdcDec_l': 0x04,
  #'REG_enableAdcDec_h': 0x10, # enable analog trigger
  
  # digital config
  'REG_enableTestOutput':     1,
  'REG_enableTestInput':      1,
  'REG_testOutputSelGroup':   1, # select groupB
  'REG_disableChannelA':      0,
  'REG_disableChannelB':      0,
  'REG_disableEpochChannelA': 1, 
  'REG_disableEpochChannelB': 1
}


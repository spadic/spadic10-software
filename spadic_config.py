#!/usr/bin/python

from spadic_registers import *


#====================================================================   
# dictionaries of default RF and SR configurations
# use these as arguments for Spadic.config()
#====================================================================   

#--------------------------------------------------------------------   
# 1) Shift register
#--------------------------------------------------------------------   

#------------------------------
# Global 
#------------------------------
SR_DEFAULT = {
    # ADC bias
    'VNDel'            : 70,    
    'VPDel'            : 100,          
    'VPLoadFB2'        : 70,
    'VPLoadFB'         : 70,
    'VPFB'             : 70,
    'VPAmp'            : 70,

    # Channel config
    'baselineTrimN'    : 10,
    'SelMonitor'       : 1, # ADC=0, CSA=1
    'DecSelectNP'      : 1, # N=0, P=1

    # N channel bias 
    'nCascN'           : 30,
    'pCascN'           : 52,
    'nSourceBiasN'     : 50,
    'pSourceBiasN'     : 70,
    'pFBN'             : 60,

    # P channel bias 
    'nCascP'           : 60,
    'pCascP'           : 60,
    'nSourceBiasP'     : 60,
    'pSourceBiasP'     : 60,
    'nFBP'             : 60
}

#------------------------------
# Channels
#------------------------------
CHANNEL_DEFAULT = {
    'baselineTrimP_' : 10,
    'ampToBus_'      : 0,
    'enMonitorAdc_'  : 0,
    'frontEndSelNP_' : 1,
    'enSignalAdc_'   : 1,
    'enAmpN_'        : 0,
    'enAmpP_'        : 0
}
for ch in range(32):
    for _reg in CHANNEL_DEFAULT:
        reg = _reg + str(ch)
        SR_DEFAULT[reg] = CHANNEL_DEFAULT[_reg]


#--------------------------------------------------------------------   
# 2) Register file
#--------------------------------------------------------------------   

RF_DEFAULT = {
   'REG_threshold1':        -255,
   'REG_threshold2':        -210,
   'REG_compDiffMode':         0,
   'REG_selectMask_h':    0xFFFF,
   'REG_selectMask_l':    0x0000,
   'REG_hitWindowLength':     16,
   'REG_disableChannelA': 0xFFFF, # disable group A
   'REG_disableChannelB': 0x7FFF, # disable group B, exept for channel 31
   'REG_enableTestOutput':     1,
   'REG_enableTestInput':      1, # for dataSync signal
   'REG_testOutputSelGroup':   1  # select test output group B

   # enable trigger channel 1 - miscInTop0 - DIP3
   #//spadicLib->writeRF(0xC0, 0xFF00);
   #//spadicLib->writeRF(0xC8, 0x03FF);
}


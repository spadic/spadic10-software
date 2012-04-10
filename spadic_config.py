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
    ###############################
    # Global 
    ###############################

    #ADC bias
    'VNDel'            : 70,    
    'VPDel'            : 100,          
    'VPLoadFB2'        : 70,
    'VPLoadFB'         : 70,
    'VPFB'             : 70,
    'VPAmp'            : 70,

    #channel config
    'baselineTrimN'    : 10,
    'SelMonitor'       : 1, #1: CSA 0: ADC
    'DecSelectNP'      : 1,

    #N channel bias 
    'nCascN'           : 30,
    'pCascN'           : 52,
    'nSourceBiasN'     : 50,
    'pSourceBiasN'     : 70,
    'pFBN'             : 60,

    #P channel bias 
    'nCascP'           : 60,
    'pCascP'           : 60,
    'nSourceBiasP'     : 60,
    'pSourceBiasP'     : 60,
    'nFBP'             : 60,

    ###############################
    # Channels
    ###############################

    #P channel 0 config 
    'baselineTrimP_0' : 30,
    'ampToBus_0'      : 0,
    'enMonitorAdc_0'  : 0,
    'frontEndSelNP_0' : 1,
    'enSignalAdc_0'   : 1,
    'enAmpN_0'        : 0,
    'enAmpP_0'        : 1,

    #P channel 1 config 
    'baselineTrimP_1' : 30,
    'ampToBus_1'      : 0,
    'enMonitorAdc_1'  : 0,
    'frontEndSelNP_1' : 1,
    'enSignalAdc_1'   : 1,
    'enAmpN_1'        : 0,
    'enAmpP_1'        : 1,

    #P channel 2 config 
    'baselineTrimP_2' : 30,
    'ampToBus_2'      : 0,
    'enMonitorAdc_2'  : 0,
    'frontEndSelNP_2' : 1,
    'enSignalAdc_2'   : 1,
    'enAmpN_2'        : 0,
    'enAmpP_2'        : 1,

    #P channel 3 config 
    'baselineTrimP_3' : 30,
    'ampToBus_3'      : 0,
    'enMonitorAdc_3'  : 0,
    'frontEndSelNP_3' : 1,
    'enSignalAdc_3'   : 1,
    'enAmpN_3'        : 0,
    'enAmpP_3'        : 1,

    #P channel 4 config 
    'baselineTrimP_4' : 30,
    'ampToBus_4'      : 0,
    'enMonitorAdc_4'  : 0,
    'frontEndSelNP_4' : 1,
    'enSignalAdc_4'   : 1,
    'enAmpN_4'        : 0,
    'enAmpP_4'        : 1,

    #P channel 5 config 
    'baselineTrimP_5' : 30,
    'ampToBus_5'      : 0,
    'enMonitorAdc_5'  : 0,
    'frontEndSelNP_5' : 1,
    'enSignalAdc_5'   : 1,
    'enAmpN_5'        : 0,
    'enAmpP_5'        : 1,

    #P channel 6 config 
    'baselineTrimP_6' : 30,
    'ampToBus_6'      : 0,
    'enMonitorAdc_6'  : 0,
    'frontEndSelNP_6' : 1,
    'enSignalAdc_6'   : 1,
    'enAmpN_6'        : 0,
    'enAmpP_6'        : 1,

    #P channel 7 config 
    'baselineTrimP_7' : 30,
    'ampToBus_7'      : 0,
    'enMonitorAdc_7'  : 0,
    'frontEndSelNP_7' : 1,
    'enSignalAdc_7'   : 1,
    'enAmpN_7'        : 0,
    'enAmpP_7'        : 1,

    #P channel 8 config 
    'baselineTrimP_8' : 30,
    'ampToBus_8'      : 0,
    'enMonitorAdc_8'  : 0,
    'frontEndSelNP_8' : 1,
    'enSignalAdc_8'   : 1,
    'enAmpN_8'        : 0,
    'enAmpP_8'        : 1,

    #P channel 9 config 
    'baselineTrimP_9' : 30,
    'ampToBus_9'      : 0,
    'enMonitorAdc_9'  : 0,
    'frontEndSelNP_9' : 1,
    'enSignalAdc_9'   : 1,
    'enAmpN_9'        : 0,
    'enAmpP_9'        : 1,

    #P channel 10 config 
    'baselineTrimP_10' : 30,
    'ampToBus_10'      : 0,
    'enMonitorAdc_10'  : 0,
    'frontEndSelNP_10' : 1,
    'enSignalAdc_10'   : 1,
    'enAmpN_10'        : 0,
    'enAmpP_10'        : 1,

    #P channel 11 config 
    'baselineTrimP_11' : 30,
    'ampToBus_11'      : 0,
    'enMonitorAdc_11'  : 0,
    'frontEndSelNP_11' : 1,
    'enSignalAdc_11'   : 1,
    'enAmpN_11'        : 0,
    'enAmpP_11'        : 1,

    #P channel 12 config 
    'baselineTrimP_12' : 30,
    'ampToBus_12'      : 0,
    'enMonitorAdc_12'  : 0,
    'frontEndSelNP_12' : 1,
    'enSignalAdc_12'   : 1,
    'enAmpN_12'        : 0,
    'enAmpP_12'        : 1,

    #P channel 13 config 
    'baselineTrimP_13' : 30,
    'ampToBus_13'      : 0,
    'enMonitorAdc_13'  : 0,
    'frontEndSelNP_13' : 1,
    'enSignalAdc_13'   : 1,
    'enAmpN_13'        : 0,
    'enAmpP_13'        : 1,

    #P channel 14 config 
    'baselineTrimP_14' : 30,
    'ampToBus_14'      : 0,
    'enMonitorAdc_14'  : 0,
    'frontEndSelNP_14' : 1,
    'enSignalAdc_14'   : 1,
    'enAmpN_14'        : 0,
    'enAmpP_14'        : 1,

    #P channel 15 config 
    'baselineTrimP_15' : 30,
    'ampToBus_15'      : 0,
    'enMonitorAdc_15'  : 0,
    'frontEndSelNP_15' : 1,
    'enSignalAdc_15'   : 1,
    'enAmpN_15'        : 0,
    'enAmpP_15'        : 1,

    #P channel 16 config 
    'baselineTrimP_16' : 30,
    'ampToBus_16'      : 0,
    'enMonitorAdc_16'  : 0,
    'frontEndSelNP_16' : 1,
    'enSignalAdc_16'   : 1,
    'enAmpN_16'        : 0,
    'enAmpP_16'        : 1,

    #P channel 17 config
    'baselineTrimP_17' : 30,
    'ampToBus_17'      : 0,
    'enMonitorAdc_17'  : 0,
    'frontEndSelNP_17' : 1,
    'enSignalAdc_17'   : 1,
    'enAmpN_17'        : 0,
    'enAmpP_17'        : 1,

    #P channel 18 config
    'baselineTrimP_18' : 30,
    'ampToBus_18'      : 0,
    'enMonitorAdc_18'  : 0,
    'frontEndSelNP_18' : 1,
    'enSignalAdc_18'   : 1,
    'enAmpN_18'        : 0,
    'enAmpP_18'        : 1,

    #P channel 19 config
    'baselineTrimP_19' : 30,
    'ampToBus_19'      : 0,
    'enMonitorAdc_19'  : 0,
    'frontEndSelNP_19' : 1,
    'enSignalAdc_19'   : 1,
    'enAmpN_19'        : 0,
    'enAmpP_19'        : 1,

    #P channel 20 config
    'baselineTrimP_20' : 30,
    'ampToBus_20'      : 0,
    'enMonitorAdc_20'  : 0,
    'frontEndSelNP_20' : 1,
    'enSignalAdc_20'   : 1,
    'enAmpN_20'        : 0,
    'enAmpP_20'        : 1,

    #P channel 21 config
    'baselineTrimP_21' : 30,
    'ampToBus_21'      : 0,
    'enMonitorAdc_21'  : 0,
    'frontEndSelNP_21' : 1,
    'enSignalAdc_21'   : 1,
    'enAmpN_21'        : 0,
    'enAmpP_21'        : 1,

    #P channel 22 config
    'baselineTrimP_22' : 30,
    'ampToBus_22'      : 0,
    'enMonitorAdc_22'  : 0,
    'frontEndSelNP_22' : 1,
    'enSignalAdc_22'   : 1,
    'enAmpN_22'        : 0,
    'enAmpP_22'        : 1,

    #P channel 23 config
    'baselineTrimP_23' : 30,
    'ampToBus_23'      : 0,
    'enMonitorAdc_23'  : 0,
    'frontEndSelNP_23' : 1,
    'enSignalAdc_23'   : 1,
    'enAmpN_23'        : 0,
    'enAmpP_23'        : 1,

    #P channel 24 config
    'baselineTrimP_24' : 30,
    'ampToBus_24'      : 0,
    'enMonitorAdc_24'  : 0,
    'frontEndSelNP_24' : 1,
    'enSignalAdc_24'   : 1,
    'enAmpN_24'        : 0,
    'enAmpP_24'        : 1,

    #P channel 25 config
    'baselineTrimP_25' : 30,
    'ampToBus_25'      : 0,
    'enMonitorAdc_25'  : 0,
    'frontEndSelNP_25' : 1,
    'enSignalAdc_25'   : 1,
    'enAmpN_25'        : 0,
    'enAmpP_25'        : 1,

    #P channel 26 config
    'baselineTrimP_26' : 30,
    'ampToBus_26'      : 0,
    'enMonitorAdc_26'  : 0,
    'frontEndSelNP_26' : 1,
    'enSignalAdc_26'   : 1,
    'enAmpN_26'        : 0,
    'enAmpP_26'        : 1,

    #P channel 27 config
    'baselineTrimP_27' : 30,
    'ampToBus_27'      : 0,
    'enMonitorAdc_27'  : 0,
    'frontEndSelNP_27' : 1,
    'enSignalAdc_27'   : 1,
    'enAmpN_27'        : 0,
    'enAmpP_27'        : 1,

    #P channel 28 config
    'baselineTrimP_28' : 30,
    'ampToBus_28'      : 0,
    'enMonitorAdc_28'  : 0,
    'frontEndSelNP_28' : 1,
    'enSignalAdc_28'   : 1,
    'enAmpN_28'        : 0,
    'enAmpP_28'        : 1,

    #P channel 29 config
    'baselineTrimP_29' : 30,
    'ampToBus_29'      : 0,
    'enMonitorAdc_29'  : 0,
    'frontEndSelNP_29' : 1,
    'enSignalAdc_29'   : 1,
    'enAmpN_29'        : 0,
    'enAmpP_29'        : 1,

    #P channel 30 config
    'baselineTrimP_30' : 30,
    'ampToBus_30'      : 0,
    'enMonitorAdc_30'  : 0,
    'frontEndSelNP_30' : 1,
    'enSignalAdc_30'   : 1,
    'enAmpN_30'        : 0,
    'enAmpP_30'        : 1,
  
    #P channel 31 config
    'baselineTrimP_31' : 10,
    'ampToBus_31'      : 0,
    'enMonitorAdc_31'  : 0,
    'frontEndSelNP_31' : 1,
    'enSignalAdc_31'   : 1,
    'enAmpN_31'        : 0,
    'enAmpP_31'        : 1
}


#--------------------------------------------------------------------   
# register file
#--------------------------------------------------------------------   

RF_DEFAULT = {
   'REG_threshold1':           2,
   'REG_threshold2':          18,
   'REG_selectMask_h':    0xFFFF,
   'REG_selectMask_l':    0x0000,
   'REG_hitWindowLength':     32,
   'REG_disableChannelA': 0xFFFF, # disable group A
   'REG_disableChannelB': 0x7FFF, # disable group B, exept for channel 31
   'REG_enableTestOutput':     1,
   'REG_enableTestInput':      1, # for dataSync signal
   'REG_testOutputSelGroup':   1  # select test output group B

   # enable trigger channel 1 - miscInTop0 - DIP3
   #//spadicLib->writeRF(0xC0, 0xFF00);
   #//spadicLib->writeRF(0xC8, 0x03FF);
}


#--------------------------------------------------------------------
# dictionary of SPADIC 1.0 register file (contains addresses)
#--------------------------------------------------------------------

RF_MAP = {
   "loopback": 0x0, # width=3, sw="rw", hw="ro"
                    # [2] DES2BS Loopback
                    # [1] BS2DEC Loopback
                    # [0] DEC2USR Loopback
                    # Sets loopback modes.

   "overrides": 0x8, # width=7, sw="rw", hw="ro"
                     # [6] link_active;
                     # [5] user_pin2;
                     # [4] user_pin1;
                     # [3] align_initovr;
                     # [2] link_ready;
                     # [1] rxpcs_initovr;
                     # [0] txpcs_initovr.
                     # Delivers user pins and override pins for link_active,
                     # align_initovr, link_ready, rxpcs_initovr, txpcs_initovr
                     # - physical link init.

   "REG_CbmNetAddr"       : 0x10, # width=16, sw="rw", hw="ro"
   "REG_EpochCounter"     : 0x18, # width=16, sw="rw", hw="ro"
   "REG_threshold1"       : 0x20, # width=9 , sw="rw", hw="ro"
   "REG_threshold2"       : 0x28, # width=9 , sw="rw", hw="ro"
   "REG_compDiffMode"     : 0x30, # width=1 , sw="rw", hw="ro"
   "REG_hitWindowLength"  : 0x38, # width=6 , sw="rw", hw="ro"
   "REG_selectMask_l"     : 0x40, # width=16, sw="rw", hw="ro"
   "REG_selectMask_h"     : 0x48, # width=16, sw="rw", hw="ro"
   "REG_bypassFilterStage": 0x50, # width=5 , sw="rw", hw="ro"
   "REG_aCoeffFilter_l"   : 0x58, # width=16, sw="rw", hw="ro"
   "REG_aCoeffFilter_h"   : 0x60, # width=2 , sw="rw", hw="ro"
   "REG_bCoeffFilter_l"   : 0x68, # width=16, sw="rw", hw="ro"
   "REG_bCoeffFilter_h"   : 0x70, # width=8 , sw="rw", hw="ro"
   "REG_scalingFilter"    : 0x78, # width=9 , sw="rw", hw="ro"
   "REG_offsetFilter"     : 0x80, # width=9 , sw="rw", hw="ro"
   "REG_groupIdA"         : 0x88, # width=8 , sw="rw", hw="ro"
   "REG_groupIdB"         : 0x90, # width=8 , sw="rw", hw="ro"
  
   # "REG_neighborSelectMatrixA"
   # "REG_neighborSelectMatrixA_H"
   # "REG_neighborSelectMatrixB"
   # "REG_neighborSelectMatrixB_H"
  
   "REG_disableChannelA"     : 0x288, # width=16, sw="rw", hw="ro"
   "REG_disableChannelB"     : 0x290, # width=16, sw="rw", hw="ro"
   "REG_disableEpochChannelA": 0x298, # width=1 , sw="rw", hw="ro"
   "REG_disableEpochChannelB": 0x2a0, # width=1 , sw="rw", hw="ro"
   "REG_enableTestOutput"    : 0x2a8, # width=1 , sw="rw", hw="ro"
   "REG_testOutputSelGroup"  : 0x2b0, # width=1 , sw="rw", hw="ro"
   "REG_enableTestInput"     : 0x2b8, # width=1 , sw="rw", hw="ro"
   "REG_enableAdcDec_l"      : 0x2c0, # width=16, sw="rw", hw="ro"
   "REG_enableAdcDec_h"      : 0x2c8, # width=5 , sw="rw", hw="ro"
   "REG_triggerMaskA"        : 0x2d0, # width=16, sw="rw", hw="ro"
   "REG_triggerMaskB"        : 0x2d8, # width=16, sw="rw", hw="ro"
   "REG_enableAnalogTrigger" : 0x2e0, # width=1 , sw="rw", hw="ro"
   "REG_enableTriggerOutput" : 0x2e8, # width=1 , sw="rw", hw="ro"
   "control"                 : 0x2f0, # width=14, sw="wo", hw="ro"
   "data"                    : 0x300,
   "status"                  : 0x2f8, # width=16, sw="ro", hw="wo"
}
 

#--------------------------------------------------------------------
# dictionary of SPADIC 1.0 shift register (contains bit numbers)
#--------------------------------------------------------------------

# length of shift register (number of bits)
SR_LENGTH = 584

SR_MAP = {
#  name : [MSB, ..., LSB]
  'dac1': [4, 2, 5, 6]
}


class Register():
    def __init__(self, desc='', address=0x00, width=0, sw='', hw=''):
        self.desc = desc,
        self.address = address,
        self.width = width
        self.sw = sw
        self.hw = hw
        
spadic_rf = {
   "loopback": Register(desc="""
[2] DES2BS Loopback;
[1] BS2DEC Loopback;
[0] DEC2USR Loopback.
Sets loopback modes.""",
     address="0x0", width="3", sw="rw", hw="ro"),

   "overrides": Register(desc="""
[6] link_active;
[5] user_pin2;
[4] user_pin1;
[3] align_initovr;
[2] link_ready;
[1] rxpcs_initovr;
[0] txpcs_initovr.
Delivers user pins and override pins for link_active, align_initovr,
link_ready, rxpcs_initovr, txpcs_initovr - physical link init.""",
     address="0x8", width="7", sw="rw", hw="ro"),

   "REG_CbmNetAddr"       : Register(address="0x10", width="16", sw="rw", hw="ro"),
   "REG_EpochCounter"     : Register(address="0x18", width="16", sw="rw", hw="ro"),
   "REG_threshold1"       : Register(address="0x20", width="9" , sw="rw", hw="ro"),
   "REG_threshold2"       : Register(address="0x28", width="9" , sw="rw", hw="ro"),
   "REG_compDiffMode"     : Register(address="0x30", width="1" , sw="rw", hw="ro"),
   "REG_hitWindowLength"  : Register(address="0x38", width="6" , sw="rw", hw="ro"),
   "REG_selectMask_l"     : Register(address="0x40", width="16", sw="rw", hw="ro"),
   "REG_selectMask_h"     : Register(address="0x48", width="16", sw="rw", hw="ro"),
   "REG_bypassFilterStage": Register(address="0x50", width="5" , sw="rw", hw="ro"),
   "REG_aCoeffFilter_l"   : Register(address="0x58", width="16", sw="rw", hw="ro"),
   "REG_aCoeffFilter_h"   : Register(address="0x60", width="2" , sw="rw", hw="ro"),
   "REG_bCoeffFilter_l"   : Register(address="0x68", width="16", sw="rw", hw="ro"),
   "REG_bCoeffFilter_h"   : Register(address="0x70", width="8" , sw="rw", hw="ro"),
   "REG_scalingFilter"    : Register(address="0x78", width="9" , sw="rw", hw="ro"),
   "REG_offsetFilter"     : Register(address="0x80", width="9" , sw="rw", hw="ro"),
   "REG_groupIdA"         : Register(address="0x88", width="8" , sw="rw", hw="ro"),
   "REG_groupIdB"         : Register(address="0x90", width="8" , sw="rw", hw="ro"),
  
   # REG_neighborSelectMatrixA
   
   # REG_neighborSelectMatrixA_H
  
   # REG_neighborSelectMatrixB
   
   # REG_neighborSelectMatrixB_H
  
   "REG_disableChannelA"     : Register(address="0x288", width="16", sw="rw", hw="ro"),
   "REG_disableChannelB"     : Register(address="0x290", width="16", sw="rw", hw="ro"),
   "REG_disableEpochChannelA": Register(address="0x298", width="1" , sw="rw", hw="ro"),
   "REG_disableEpochChannelB": Register(address="0x2a0", width="1" , sw="rw", hw="ro"),
   "REG_enableTestOutput"    : Register(address="0x2a8", width="1" , sw="rw", hw="ro"),
   "REG_testOutputSelGroup"  : Register(address="0x2b0", width="1" , sw="rw", hw="ro"),
   "REG_enableTestInput"     : Register(address="0x2b8", width="1" , sw="rw", hw="ro"),
   "REG_enableAdcDec_l"      : Register(address="0x2c0", width="16", sw="rw", hw="ro"),
   "REG_enableAdcDec_h"      : Register(address="0x2c8", width="5" , sw="rw", hw="ro"),
   "REG_triggerMaskA"        : Register(address="0x2d0", width="16", sw="rw", hw="ro"),
   "REG_triggerMaskB"        : Register(address="0x2d8", width="16", sw="rw", hw="ro"),
   "REG_enableAnalogTrigger" : Register(address="0x2e0", width="1" , sw="rw", hw="ro"),
   "REG_enableTriggerOutput" : Register(address="0x2e8", width="1" , sw="rw", hw="ro"),
   "control"                 : Register(address="0x2f0", width="14", sw="wo", hw="ro"),
   "status"                  : Register(address="0x2f8", width="16", sw="ro", hw="wo")
}
  

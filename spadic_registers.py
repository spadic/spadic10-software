from bit_byte_helper import *


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
#  name             : [MSB, ..., LSB]    # MSB:LSB   default

  'VNDel'           : range(  1,   7+1), #   7:1     0
  'VPDel'           : range(  9,  15+1), #  15:9     0
  'VPLoadFB2'       : range( 17,  23+1), #  23:17    0
  'VPLoadFB'        : range( 25,  31+1), #  31:25    0
  'VPFB'            : range( 33,  39+1), #  39:33    0
  'VPAmp'           : range( 41,  47+1), #  47:41    0
  'baselineTrimN'   : range( 49,  55+1), #  55:49    0
                             
  'DecSelectNP'     : range( 56,  56+1), #  56:56    1
  'pCascP'          : range( 57,  63+1), #  63:57    0
  'SelMonitor'      : range( 64,  64+1), #  64:64    0
  'nCascP'          : range( 65,  71+1), #  71:65    0
  'pSourceBiasN'    : range( 73,  79+1), #  79:73    0
  'pSourceBiasP'    : range( 81,  87+1), #  87:81    0
  'nSourceBiasN'    : range( 89,  95+1), #  95:89    0
  'nSourceBiasP'    : range( 97, 103+1), # 103:97    0
  'pFBN'            : range(105, 111+1), # 111:105   0
  'nFBP'            : range(113, 119+1), # 119:113   0
  'pCascN'          : range(121, 127+1), # 127:121   0
  'nCascN'          : range(129, 135+1), # 135:129   0

  'baselineTrimP_0' : range(137, 143+1), # 143:137   0
  'enSignalAdc_0'   : range(144, 144+1), # 144:144   0
  'enMonitorAdc_0'  : range(145, 145+1), # 145:145   0
  'ampToBus_0'      : range(146, 146+1), # 146:146   0
  'enAmpP_0'        : range(147, 147+1), # 147:147   0
  'frontEndSelNP_0' : range(148, 148+1), # 148:148   0
  'enAmpN_0'        : range(149, 149+1), # 149:149   1

  'baselineTrimP_1' : range(151, 157+1), # 157:151   0
  'enSignalAdc_1'   : range(158, 158+1), # 158:158   0
  'enMonitorAdc_1'  : range(159, 159+1), # 159:159   0
  'ampToBus_1'      : range(160, 160+1), # 160:160   0
  'enAmpP_1'        : range(161, 161+1), # 161:161   0
  'frontEndSelNP_1' : range(162, 162+1), # 162:162   0
  'enAmpN_1'        : range(163, 163+1), # 163:163   1

  'baselineTrimP_2' : range(165, 171+1), # 171:165   0
  'enSignalAdc_2'   : range(172, 172+1), # 172:172   0
  'enMonitorAdc_2'  : range(173, 173+1), # 173:173   0
  'ampToBus_2'      : range(174, 174+1), # 174:174   0
  'enAmpP_2'        : range(175, 175+1), # 175:175   0
  'frontEndSelNP_2' : range(176, 176+1), # 176:176   0
  'enAmpN_2'        : range(177, 177+1), # 177:177   1

  'baselineTrimP_3' : range(179, 185+1), # 185:179   0
  'enSignalAdc_3'   : range(186, 186+1), # 186:186   0
  'enMonitorAdc_3'  : range(187, 187+1), # 187:187   0
  'ampToBus_3'      : range(188, 188+1), # 188:188   0
  'enAmpP_3'        : range(189, 189+1), # 189:189   0
  'frontEndSelNP_3' : range(190, 190+1), # 190:190   0
  'enAmpN_3'        : range(191, 191+1), # 191:191   1

  'baselineTrimP_4' : range(193, 199+1), # 199:193   0
  'enSignalAdc_4'   : range(200, 200+1), # 200:200   0
  'enMonitorAdc_4'  : range(201, 201+1), # 201:201   0
  'ampToBus_4'      : range(202, 202+1), # 202:202   0
  'enAmpP_4'        : range(203, 203+1), # 203:203   0
  'frontEndSelNP_4' : range(204, 204+1), # 204:204   0
  'enAmpN_4'        : range(205, 205+1), # 205:205   1

  'baselineTrimP_5' : range(207, 213+1), # 213:207   0
  'enSignalAdc_5'   : range(214, 214+1), # 214:214   0
  'enMonitorAdc_5'  : range(215, 215+1), # 215:215   0
  'ampToBus_5'      : range(216, 216+1), # 216:216   0
  'enAmpP_5'        : range(217, 217+1), # 217:217   0
  'frontEndSelNP_5' : range(218, 218+1), # 218:218   0
  'enAmpN_5'        : range(219, 219+1), # 219:219   1

  'baselineTrimP_6' : range(221, 227+1), # 227:221   0
  'enSignalAdc_6'   : range(228, 228+1), # 228:228   0
  'enMonitorAdc_6'  : range(229, 229+1), # 229:229   0
  'ampToBus_6'      : range(230, 230+1), # 230:230   0
  'enAmpP_6'        : range(231, 231+1), # 231:231   0
  'frontEndSelNP_6' : range(232, 232+1), # 232:232   0
  'enAmpN_6'        : range(233, 233+1), # 233:233   1

  'baselineTrimP_7' : range(235, 241+1), # 241:235   0
  'enSignalAdc_7'   : range(242, 242+1), # 242:242   0
  'enMonitorAdc_7'  : range(243, 243+1), # 243:243   0
  'ampToBus_7'      : range(244, 244+1), # 244:244   0
  'enAmpP_7'        : range(245, 245+1), # 245:245   0
  'frontEndSelNP_7' : range(246, 246+1), # 246:246   0
  'enAmpN_7'        : range(247, 247+1), # 247:247   1

  'baselineTrimP_8' : range(249, 255+1), # 255:249   0
  'enSignalAdc_8'   : range(256, 256+1), # 256:256   0
  'enMonitorAdc_8'  : range(257, 257+1), # 257:257   0
  'ampToBus_8'      : range(258, 258+1), # 258:258   0
  'enAmpP_8'        : range(259, 259+1), # 259:259   0
  'frontEndSelNP_8' : range(260, 260+1), # 260:260   0
  'enAmpN_8'        : range(261, 261+1), # 261:261   1

  'baselineTrimP_9' : range(263, 269+1), # 269:263   0
  'enSignalAdc_9'   : range(270, 270+1), # 270:270   0
  'enMonitorAdc_9'  : range(271, 271+1), # 271:271   0
  'ampToBus_9'      : range(272, 272+1), # 272:272   0
  'enAmpP_9'        : range(273, 273+1), # 273:273   0
  'frontEndSelNP_9' : range(274, 274+1), # 274:274   0
  'enAmpN_9'        : range(275, 275+1), # 275:275   1

  'baselineTrimP_10': range(277, 283+1), # 283:277   0
  'enSignalAdc_10'  : range(284, 284+1), # 284:284   0
  'enMonitorAdc_10' : range(285, 285+1), # 285:285   0
  'ampToBus_10'     : range(286, 286+1), # 286:286   0
  'enAmpP_10'       : range(287, 287+1), # 287:287   0
  'frontEndSelNP_10': range(288, 288+1), # 288:288   0
  'enAmpN_10'       : range(289, 289+1), # 289:289   1

  'baselineTrimP_11': range(291, 297+1), # 297:291   0
  'enSignalAdc_11'  : range(298, 298+1), # 298:298   0
  'enMonitorAdc_11' : range(299, 299+1), # 299:299   0
  'ampToBus_11'     : range(300, 300+1), # 300:300   0
  'enAmpP_11'       : range(301, 301+1), # 301:301   0
  'frontEndSelNP_11': range(302, 302+1), # 302:302   0
  'enAmpN_11'       : range(303, 303+1), # 303:303   1

  'baselineTrimP_12': range(305, 311+1), # 311:305   0
  'enSignalAdc_12'  : range(312, 312+1), # 312:312   0
  'enMonitorAdc_12' : range(313, 313+1), # 313:313   0
  'ampToBus_12'     : range(314, 314+1), # 314:314   0
  'enAmpP_12'       : range(315, 315+1), # 315:315   0
  'frontEndSelNP_12': range(316, 316+1), # 316:316   0
  'enAmpN_12'       : range(317, 317+1), # 317:317   1

  'baselineTrimP_13': range(319, 325+1), # 325:319   0
  'enSignalAdc_13'  : range(326, 326+1), # 326:326   0
  'enMonitorAdc_13' : range(327, 327+1), # 327:327   0
  'ampToBus_13'     : range(328, 328+1), # 328:328   0
  'enAmpP_13'       : range(329, 329+1), # 329:329   0
  'frontEndSelNP_13': range(330, 330+1), # 330:330   0
  'enAmpN_13'       : range(331, 331+1), # 331:331   1

  'baselineTrimP_14': range(333, 339+1), # 339:333   0
  'enSignalAdc_14'  : range(340, 340+1), # 340:340   0
  'enMonitorAdc_14' : range(341, 341+1), # 341:341   0
  'ampToBus_14'     : range(342, 342+1), # 342:342   0
  'enAmpP_14'       : range(343, 343+1), # 343:343   0
  'frontEndSelNP_14': range(344, 344+1), # 344:344   0
  'enAmpN_14'       : range(345, 345+1), # 345:345   1

  'baselineTrimP_15': range(347, 353+1), # 353:347   0
  'enSignalAdc_15'  : range(354, 354+1), # 354:354   0
  'enMonitorAdc_15' : range(355, 355+1), # 355:355   0
  'ampToBus_15'     : range(356, 356+1), # 356:356   0
  'enAmpP_15'       : range(357, 357+1), # 357:357   0
  'frontEndSelNP_15': range(358, 358+1), # 358:358   0
  'enAmpN_15'       : range(359, 359+1), # 359:359   1

  'baselineTrimP_16': range(361, 367+1), # 367:361   0
  'enSignalAdc_16'  : range(368, 368+1), # 368:368   0
  'enMonitorAdc_16' : range(369, 369+1), # 369:369   0
  'ampToBus_16'     : range(370, 370+1), # 370:370   0
  'enAmpP_16'       : range(371, 371+1), # 371:371   0
  'frontEndSelNP_16': range(372, 372+1), # 372:372   0
  'enAmpN_16'       : range(373, 373+1), # 373:373   1

  'baselineTrimP_17': range(375, 381+1), # 381:375   0
  'enSignalAdc_17'  : range(382, 382+1), # 382:382   0
  'enMonitorAdc_17' : range(383, 383+1), # 383:383   0
  'ampToBus_17'     : range(384, 384+1), # 384:384   0
  'enAmpP_17'       : range(385, 385+1), # 385:385   0
  'frontEndSelNP_17': range(386, 386+1), # 386:386   0
  'enAmpN_17'       : range(387, 387+1), # 387:387   1

  'baselineTrimP_18': range(389, 395+1), # 395:389   0
  'enSignalAdc_18'  : range(396, 396+1), # 396:396   0
  'enMonitorAdc_18' : range(397, 397+1), # 397:397   0
  'ampToBus_18'     : range(398, 398+1), # 398:398   0
  'enAmpP_18'       : range(399, 399+1), # 399:399   0
  'frontEndSelNP_18': range(400, 400+1), # 400:400   0
  'enAmpN_18'       : range(401, 401+1), # 401:401   1

  'baselineTrimP_19': range(403, 409+1), # 409:403   0
  'enSignalAdc_19'  : range(410, 410+1), # 410:410   0
  'enMonitorAdc_19' : range(411, 411+1), # 411:411   0
  'ampToBus_19'     : range(412, 412+1), # 412:412   0
  'enAmpP_19'       : range(413, 413+1), # 413:413   0
  'frontEndSelNP_19': range(414, 414+1), # 414:414   0
  'enAmpN_19'       : range(415, 415+1), # 415:415   1

  'baselineTrimP_20': range(417, 423+1), # 423:417   0
  'enSignalAdc_20'  : range(424, 424+1), # 424:424   0
  'enMonitorAdc_20' : range(425, 425+1), # 425:425   0
  'ampToBus_20'     : range(426, 426+1), # 426:426   0
  'enAmpP_20'       : range(427, 427+1), # 427:427   0
  'frontEndSelNP_20': range(428, 428+1), # 428:428   0
  'enAmpN_20'       : range(429, 429+1), # 429:429   1

  'baselineTrimP_21': range(431, 437+1), # 437:431   0
  'enSignalAdc_21'  : range(438, 438+1), # 438:438   0
  'enMonitorAdc_21' : range(439, 439+1), # 439:439   0
  'ampToBus_21'     : range(440, 440+1), # 440:440   0
  'enAmpP_21'       : range(441, 441+1), # 441:441   0
  'frontEndSelNP_21': range(442, 442+1), # 442:442   0
  'enAmpN_21'       : range(443, 443+1), # 443:443   1

  'baselineTrimP_22': range(445, 451+1), # 451:445   0
  'enSignalAdc_22'  : range(452, 452+1), # 452:452   0
  'enMonitorAdc_22' : range(453, 453+1), # 453:453   0
  'ampToBus_22'     : range(454, 454+1), # 454:454   0
  'enAmpP_22'       : range(455, 455+1), # 455:455   0
  'frontEndSelNP_22': range(456, 456+1), # 456:456   0
  'enAmpN_22'       : range(457, 457+1), # 457:457   1

  'baselineTrimP_23': range(459, 465+1), # 465:459   0
  'enSignalAdc_23'  : range(466, 466+1), # 466:466   0
  'enMonitorAdc_23' : range(467, 467+1), # 467:467   0
  'ampToBus_23'     : range(468, 468+1), # 468:468   0
  'enAmpP_23'       : range(469, 469+1), # 469:469   0
  'frontEndSelNP_23': range(470, 470+1), # 470:470   0
  'enAmpN_23'       : range(471, 471+1), # 471:471   1

  'baselineTrimP_24': range(473, 479+1), # 479:473   0
  'enSignalAdc_24'  : range(480, 480+1), # 480:480   0
  'enMonitorAdc_24' : range(481, 481+1), # 481:481   0
  'ampToBus_24'     : range(482, 482+1), # 482:482   0
  'enAmpP_24'       : range(483, 483+1), # 483:483   0
  'frontEndSelNP_24': range(484, 484+1), # 484:484   0
  'enAmpN_24'       : range(485, 485+1), # 485:485   1

  'baselineTrimP_25': range(487, 493+1), # 493:487   0
  'enSignalAdc_25'  : range(494, 494+1), # 494:494   0
  'enMonitorAdc_25' : range(495, 495+1), # 495:495   0
  'ampToBus_25'     : range(496, 496+1), # 496:496   0
  'enAmpP_25'       : range(497, 497+1), # 497:497   0
  'frontEndSelNP_25': range(498, 498+1), # 498:498   0
  'enAmpN_25'       : range(499, 499+1), # 499:499   1

  'baselineTrimP_26': range(501, 507+1), # 507:501   0
  'enSignalAdc_26'  : range(508, 508+1), # 508:508   0
  'enMonitorAdc_26' : range(509, 509+1), # 509:509   0
  'ampToBus_26'     : range(510, 510+1), # 510:510   0
  'enAmpP_26'       : range(511, 511+1), # 511:511   0
  'frontEndSelNP_26': range(512, 512+1), # 512:512   0
  'enAmpN_26'       : range(513, 513+1), # 513:513   1

  'baselineTrimP_27': range(515, 521+1), # 521:515   0
  'enSignalAdc_27'  : range(522, 522+1), # 522:522   0
  'enMonitorAdc_27' : range(523, 523+1), # 523:523   0
  'ampToBus_27'     : range(524, 524+1), # 524:524   0
  'enAmpP_27'       : range(525, 525+1), # 525:525   0
  'frontEndSelNP_27': range(526, 526+1), # 526:526   0
  'enAmpN_27'       : range(527, 527+1), # 527:527   1

  'baselineTrimP_28': range(529, 535+1), # 535:529   0
  'enSignalAdc_28'  : range(536, 536+1), # 536:536   0
  'enMonitorAdc_28' : range(537, 537+1), # 537:537   0
  'ampToBus_28'     : range(538, 538+1), # 538:538   0
  'enAmpP_28'       : range(539, 539+1), # 539:539   0
  'frontEndSelNP_28': range(540, 540+1), # 540:540   0
  'enAmpN_28'       : range(541, 541+1), # 541:541   1

  'baselineTrimP_29': range(543, 549+1), # 549:543   0
  'enSignalAdc_29'  : range(550, 550+1), # 550:550   0
  'enMonitorAdc_29' : range(551, 551+1), # 551:551   0
  'ampToBus_29'     : range(552, 552+1), # 552:552   0
  'enAmpP_29'       : range(553, 553+1), # 553:553   0
  'frontEndSelNP_29': range(554, 554+1), # 554:554   0
  'enAmpN_29'       : range(555, 555+1), # 555:555   1

  'baselineTrimP_30': range(557, 563+1), # 563:557   0
  'enSignalAdc_30'  : range(564, 564+1), # 564:564   0
  'enMonitorAdc_30' : range(565, 565+1), # 565:565   0
  'ampToBus_30'     : range(566, 566+1), # 566:566   0
  'enAmpP_30'       : range(567, 567+1), # 567:567   0
  'frontEndSelNP_30': range(568, 568+1), # 568:568   0
  'enAmpN_30'       : range(569, 569+1), # 569:569   1

  'baselineTrimP_31': range(571, 577+1), # 577:571   0
  'enSignalAdc_31'  : range(578, 578+1), # 578:578   0
  'enMonitorAdc_31' : range(579, 579+1), # 579:579   0
  'ampToBus_31'     : range(580, 580+1), # 580:580   0
  'enAmpP_31'       : range(581, 581+1), # 581:581   0
  'frontEndSelNP_31': range(582, 582+1), # 582:582   0
  'enAmpN_31'       : range(583, 583+1), # 583:583   1
}


#--------------------------------------------------------------------
# SPADIC Shift Register representation
#--------------------------------------------------------------------

class SpadicShiftRegister:
    def __init__(self):
        self.bits = ['0']*SR_LENGTH
        # bits[0] = MSB (on the left side, shifted last)
        # bits[-1] = LSB (on the right side, shifted first)

    def __str__(self):
        return ''.join(self.bits)
        # use this as argument for SpadicI2cRf.write_shiftregister

    def set_value(self, name, value):
        pos = SR_MAP[name]
        n = len(pos)
        for (i, b) in enumerate(int2bitstring(value, n)):
            self.bits[pos[i]] = b

    def get_value(self, name):
        return int(''.join([self.bits[p] for p in SR_MAP[name]]), 2)


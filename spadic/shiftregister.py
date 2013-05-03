# Throughout this file, the "binary representation" of an n-bit number will
# be a string of '0' and '1' characters, with the LSB at position 0 (to
# the left) and the MSB at position n-1 (to the right)

def int2bitstring(x, n):
    """Convert an integer to its binary representation."""
    x += 2**n                # support two's complement
    s = bin(x)[2:]           # remove '0b' at the beginning
    s = s.rjust(n, '0')[-n:] # make string of length n
    return ''.join(reversed(s))


#====================================================================
# generic shift register representation
#====================================================================

class ShiftRegisterEntry:
    """Representation of a single entry in a shift register."""
    def __init__(self, positions):
        """Set the bit positions belonging to the entry."""
        self.positions = positions
        self.size = len(positions)
        self._value = 0

    def set(self, value):
        """Set the value."""
        v = value % (2**self.size)
        if v != self._value:
            self._value = v

    def get(self):
        """Get the value."""
        return self._value


class ShiftRegister:
    """Representation of a generic shift register."""

    def __init__(self, length, register_map):
        """Set up all registers."""
        self._length = length

        self._registers = {}
        for (name, positions) in register_map.iteritems():
            r = ShiftRegisterEntry(positions)
            self._registers[name] = r

        self._last_bits = None
        self._known = False

        # emulate dictionary behaviour (read-only)
        self.__contains__ = self._registers.__contains__
        self.__iter__     = self._registers.__iter__
        self.__getitem__  = self._registers.__getitem__


    def _write(self, bits):
        raise NotImplementedError(
            "Overwrite this with the hardware write operation.")

    def _read(self):
        raise NotImplementedError(
            "Overwrite this with the hardware read operation.")


    def _to_bits(self):
        """Generate bit string from configuration."""
        bits = ['0']*self._length
        for name in self:
            pos = self[name].positions
            n = self[name].size
            value = self[name].get()
            for (i, b) in enumerate(int2bitstring(value, n)):
                bits[pos[i]] = b
        return ''.join(bits)

    def _from_bits(self, bits):
        """Extract configuration from bit string."""
        for name in self:
            pos = self[name].positions
            n = self[name].size
            value_bits = ['0']*n
            for i in range(n):
                value_bits[i] = bits[pos[i]]
            value = int(''.join(reversed(value_bits)), 2)
            self[name].set(value)


    def set(self, config):
        """Set the configuration without performing the write operation."""
        for name in config:
            self[name].set(config[name])

    def get(self):
        """Get the configuration without performing the read operation."""
        config = {}
        for name in self:
            config[name] = self[name].get()
        return config

    def apply(self):
        """Perform the write operation."""
        bits = self._to_bits()
        if bits != self._last_bits:
            self._write(bits)
            self._last_bits = bits
            self._known = False

    def update(self):
        """Perform the read operation."""
        if not self._known or self._last_bits != self._to_bits():
            bits = self._read()
            self._from_bits(bits)
            self._last_bits = bits
            self._known = True

    def clear(self):
        """Set all shift register entries to zero."""
        for name in self:
            self[name].set(0)
        self.apply()

    def write(self, config):
        """Write the configuration contained in a dictionary.

        Has the same effect as calling "set" and then "apply".
        """
        self.set(config)
        self.apply()

    def read(self):
        """Read the configuration into a dictionary.

        Has the same effect as calling "update" and then "get".
        """
        self.update()
        return self.get()


#====================================================================
# representation of the SPADIC 1.0 shift register
#====================================================================

#--------------------------------------------------------------------
# map of the shift register
#--------------------------------------------------------------------
SPADIC_SR_LENGTH = 584

SPADIC_SR = {
# name              : [LSB, ..., MSB]    # MSB:LSB

  'VNDel'           : range(  1,   7+1), #   7:1
  'VPDel'           : range(  9,  15+1), #  15:9
  'VPLoadFB2'       : range( 17,  23+1), #  23:17
  'VPLoadFB'        : range( 25,  31+1), #  31:25
  'VPFB'            : range( 33,  39+1), #  39:33
  'VPAmp'           : range( 41,  47+1), #  47:41
  'baselineTrimN'   : range( 49,  55+1), #  55:49

  'DecSelectNP'     : range( 56,  56+1), #  56:56
  'pCascP'          : range( 57,  63+1), #  63:57
  'SelMonitor'      : range( 64,  64+1), #  64:64
  'nCascP'          : range( 65,  71+1), #  71:65
  'pSourceBiasN'    : range( 73,  79+1), #  79:73
  'pSourceBiasP'    : range( 81,  87+1), #  87:81
  'nSourceBiasN'    : range( 89,  95+1), #  95:89
  'nSourceBiasP'    : range( 97, 103+1), # 103:97
  'pFBN'            : range(105, 111+1), # 111:105
  'nFBP'            : range(113, 119+1), # 119:113
  'pCascN'          : range(121, 127+1), # 127:121
  'nCascN'          : range(129, 135+1), # 135:129

  'baselineTrimP_0' : range(137, 143+1), # 143:137
  'enSignalAdc_0'   : range(144, 144+1), # 144:144
  'enMonitorAdc_0'  : range(145, 145+1), # 145:145
  'ampToBus_0'      : range(146, 146+1), # 146:146
  'enAmpP_0'        : range(147, 147+1), # 147:147
  'frontEndSelNP_0' : range(148, 148+1), # 148:148
  'enAmpN_0'        : range(149, 149+1), # 149:149

  'baselineTrimP_1' : range(151, 157+1), # 157:151
  'enSignalAdc_1'   : range(158, 158+1), # 158:158
  'enMonitorAdc_1'  : range(159, 159+1), # 159:159
  'ampToBus_1'      : range(160, 160+1), # 160:160
  'enAmpP_1'        : range(161, 161+1), # 161:161
  'frontEndSelNP_1' : range(162, 162+1), # 162:162
  'enAmpN_1'        : range(163, 163+1), # 163:163

  'baselineTrimP_2' : range(165, 171+1), # 171:165
  'enSignalAdc_2'   : range(172, 172+1), # 172:172
  'enMonitorAdc_2'  : range(173, 173+1), # 173:173
  'ampToBus_2'      : range(174, 174+1), # 174:174
  'enAmpP_2'        : range(175, 175+1), # 175:175
  'frontEndSelNP_2' : range(176, 176+1), # 176:176
  'enAmpN_2'        : range(177, 177+1), # 177:177

  'baselineTrimP_3' : range(179, 185+1), # 185:179
  'enSignalAdc_3'   : range(186, 186+1), # 186:186
  'enMonitorAdc_3'  : range(187, 187+1), # 187:187
  'ampToBus_3'      : range(188, 188+1), # 188:188
  'enAmpP_3'        : range(189, 189+1), # 189:189
  'frontEndSelNP_3' : range(190, 190+1), # 190:190
  'enAmpN_3'        : range(191, 191+1), # 191:191

  'baselineTrimP_4' : range(193, 199+1), # 199:193
  'enSignalAdc_4'   : range(200, 200+1), # 200:200
  'enMonitorAdc_4'  : range(201, 201+1), # 201:201
  'ampToBus_4'      : range(202, 202+1), # 202:202
  'enAmpP_4'        : range(203, 203+1), # 203:203
  'frontEndSelNP_4' : range(204, 204+1), # 204:204
  'enAmpN_4'        : range(205, 205+1), # 205:205

  'baselineTrimP_5' : range(207, 213+1), # 213:207
  'enSignalAdc_5'   : range(214, 214+1), # 214:214
  'enMonitorAdc_5'  : range(215, 215+1), # 215:215
  'ampToBus_5'      : range(216, 216+1), # 216:216
  'enAmpP_5'        : range(217, 217+1), # 217:217
  'frontEndSelNP_5' : range(218, 218+1), # 218:218
  'enAmpN_5'        : range(219, 219+1), # 219:219

  'baselineTrimP_6' : range(221, 227+1), # 227:221
  'enSignalAdc_6'   : range(228, 228+1), # 228:228
  'enMonitorAdc_6'  : range(229, 229+1), # 229:229
  'ampToBus_6'      : range(230, 230+1), # 230:230
  'enAmpP_6'        : range(231, 231+1), # 231:231
  'frontEndSelNP_6' : range(232, 232+1), # 232:232
  'enAmpN_6'        : range(233, 233+1), # 233:233

  'baselineTrimP_7' : range(235, 241+1), # 241:235
  'enSignalAdc_7'   : range(242, 242+1), # 242:242
  'enMonitorAdc_7'  : range(243, 243+1), # 243:243
  'ampToBus_7'      : range(244, 244+1), # 244:244
  'enAmpP_7'        : range(245, 245+1), # 245:245
  'frontEndSelNP_7' : range(246, 246+1), # 246:246
  'enAmpN_7'        : range(247, 247+1), # 247:247

  'baselineTrimP_8' : range(249, 255+1), # 255:249
  'enSignalAdc_8'   : range(256, 256+1), # 256:256
  'enMonitorAdc_8'  : range(257, 257+1), # 257:257
  'ampToBus_8'      : range(258, 258+1), # 258:258
  'enAmpP_8'        : range(259, 259+1), # 259:259
  'frontEndSelNP_8' : range(260, 260+1), # 260:260
  'enAmpN_8'        : range(261, 261+1), # 261:261

  'baselineTrimP_9' : range(263, 269+1), # 269:263
  'enSignalAdc_9'   : range(270, 270+1), # 270:270
  'enMonitorAdc_9'  : range(271, 271+1), # 271:271
  'ampToBus_9'      : range(272, 272+1), # 272:272
  'enAmpP_9'        : range(273, 273+1), # 273:273
  'frontEndSelNP_9' : range(274, 274+1), # 274:274
  'enAmpN_9'        : range(275, 275+1), # 275:275

  'baselineTrimP_10': range(277, 283+1), # 283:277
  'enSignalAdc_10'  : range(284, 284+1), # 284:284
  'enMonitorAdc_10' : range(285, 285+1), # 285:285
  'ampToBus_10'     : range(286, 286+1), # 286:286
  'enAmpP_10'       : range(287, 287+1), # 287:287
  'frontEndSelNP_10': range(288, 288+1), # 288:288
  'enAmpN_10'       : range(289, 289+1), # 289:289

  'baselineTrimP_11': range(291, 297+1), # 297:291
  'enSignalAdc_11'  : range(298, 298+1), # 298:298
  'enMonitorAdc_11' : range(299, 299+1), # 299:299
  'ampToBus_11'     : range(300, 300+1), # 300:300
  'enAmpP_11'       : range(301, 301+1), # 301:301
  'frontEndSelNP_11': range(302, 302+1), # 302:302
  'enAmpN_11'       : range(303, 303+1), # 303:303

  'baselineTrimP_12': range(305, 311+1), # 311:305
  'enSignalAdc_12'  : range(312, 312+1), # 312:312
  'enMonitorAdc_12' : range(313, 313+1), # 313:313
  'ampToBus_12'     : range(314, 314+1), # 314:314
  'enAmpP_12'       : range(315, 315+1), # 315:315
  'frontEndSelNP_12': range(316, 316+1), # 316:316
  'enAmpN_12'       : range(317, 317+1), # 317:317

  'baselineTrimP_13': range(319, 325+1), # 325:319
  'enSignalAdc_13'  : range(326, 326+1), # 326:326
  'enMonitorAdc_13' : range(327, 327+1), # 327:327
  'ampToBus_13'     : range(328, 328+1), # 328:328
  'enAmpP_13'       : range(329, 329+1), # 329:329
  'frontEndSelNP_13': range(330, 330+1), # 330:330
  'enAmpN_13'       : range(331, 331+1), # 331:331

  'baselineTrimP_14': range(333, 339+1), # 339:333
  'enSignalAdc_14'  : range(340, 340+1), # 340:340
  'enMonitorAdc_14' : range(341, 341+1), # 341:341
  'ampToBus_14'     : range(342, 342+1), # 342:342
  'enAmpP_14'       : range(343, 343+1), # 343:343
  'frontEndSelNP_14': range(344, 344+1), # 344:344
  'enAmpN_14'       : range(345, 345+1), # 345:345

  'baselineTrimP_15': range(347, 353+1), # 353:347
  'enSignalAdc_15'  : range(354, 354+1), # 354:354
  'enMonitorAdc_15' : range(355, 355+1), # 355:355
  'ampToBus_15'     : range(356, 356+1), # 356:356
  'enAmpP_15'       : range(357, 357+1), # 357:357
  'frontEndSelNP_15': range(358, 358+1), # 358:358
  'enAmpN_15'       : range(359, 359+1), # 359:359

  'baselineTrimP_16': range(361, 367+1), # 367:361
  'enSignalAdc_16'  : range(368, 368+1), # 368:368
  'enMonitorAdc_16' : range(369, 369+1), # 369:369
  'ampToBus_16'     : range(370, 370+1), # 370:370
  'enAmpP_16'       : range(371, 371+1), # 371:371
  'frontEndSelNP_16': range(372, 372+1), # 372:372
  'enAmpN_16'       : range(373, 373+1), # 373:373

  'baselineTrimP_17': range(375, 381+1), # 381:375
  'enSignalAdc_17'  : range(382, 382+1), # 382:382
  'enMonitorAdc_17' : range(383, 383+1), # 383:383
  'ampToBus_17'     : range(384, 384+1), # 384:384
  'enAmpP_17'       : range(385, 385+1), # 385:385
  'frontEndSelNP_17': range(386, 386+1), # 386:386
  'enAmpN_17'       : range(387, 387+1), # 387:387

  'baselineTrimP_18': range(389, 395+1), # 395:389
  'enSignalAdc_18'  : range(396, 396+1), # 396:396
  'enMonitorAdc_18' : range(397, 397+1), # 397:397
  'ampToBus_18'     : range(398, 398+1), # 398:398
  'enAmpP_18'       : range(399, 399+1), # 399:399
  'frontEndSelNP_18': range(400, 400+1), # 400:400
  'enAmpN_18'       : range(401, 401+1), # 401:401

  'baselineTrimP_19': range(403, 409+1), # 409:403
  'enSignalAdc_19'  : range(410, 410+1), # 410:410
  'enMonitorAdc_19' : range(411, 411+1), # 411:411
  'ampToBus_19'     : range(412, 412+1), # 412:412
  'enAmpP_19'       : range(413, 413+1), # 413:413
  'frontEndSelNP_19': range(414, 414+1), # 414:414
  'enAmpN_19'       : range(415, 415+1), # 415:415

  'baselineTrimP_20': range(417, 423+1), # 423:417
  'enSignalAdc_20'  : range(424, 424+1), # 424:424
  'enMonitorAdc_20' : range(425, 425+1), # 425:425
  'ampToBus_20'     : range(426, 426+1), # 426:426
  'enAmpP_20'       : range(427, 427+1), # 427:427
  'frontEndSelNP_20': range(428, 428+1), # 428:428
  'enAmpN_20'       : range(429, 429+1), # 429:429

  'baselineTrimP_21': range(431, 437+1), # 437:431
  'enSignalAdc_21'  : range(438, 438+1), # 438:438
  'enMonitorAdc_21' : range(439, 439+1), # 439:439
  'ampToBus_21'     : range(440, 440+1), # 440:440
  'enAmpP_21'       : range(441, 441+1), # 441:441
  'frontEndSelNP_21': range(442, 442+1), # 442:442
  'enAmpN_21'       : range(443, 443+1), # 443:443

  'baselineTrimP_22': range(445, 451+1), # 451:445
  'enSignalAdc_22'  : range(452, 452+1), # 452:452
  'enMonitorAdc_22' : range(453, 453+1), # 453:453
  'ampToBus_22'     : range(454, 454+1), # 454:454
  'enAmpP_22'       : range(455, 455+1), # 455:455
  'frontEndSelNP_22': range(456, 456+1), # 456:456
  'enAmpN_22'       : range(457, 457+1), # 457:457

  'baselineTrimP_23': range(459, 465+1), # 465:459
  'enSignalAdc_23'  : range(466, 466+1), # 466:466
  'enMonitorAdc_23' : range(467, 467+1), # 467:467
  'ampToBus_23'     : range(468, 468+1), # 468:468
  'enAmpP_23'       : range(469, 469+1), # 469:469
  'frontEndSelNP_23': range(470, 470+1), # 470:470
  'enAmpN_23'       : range(471, 471+1), # 471:471

  'baselineTrimP_24': range(473, 479+1), # 479:473
  'enSignalAdc_24'  : range(480, 480+1), # 480:480
  'enMonitorAdc_24' : range(481, 481+1), # 481:481
  'ampToBus_24'     : range(482, 482+1), # 482:482
  'enAmpP_24'       : range(483, 483+1), # 483:483
  'frontEndSelNP_24': range(484, 484+1), # 484:484
  'enAmpN_24'       : range(485, 485+1), # 485:485

  'baselineTrimP_25': range(487, 493+1), # 493:487
  'enSignalAdc_25'  : range(494, 494+1), # 494:494
  'enMonitorAdc_25' : range(495, 495+1), # 495:495
  'ampToBus_25'     : range(496, 496+1), # 496:496
  'enAmpP_25'       : range(497, 497+1), # 497:497
  'frontEndSelNP_25': range(498, 498+1), # 498:498
  'enAmpN_25'       : range(499, 499+1), # 499:499

  'baselineTrimP_26': range(501, 507+1), # 507:501
  'enSignalAdc_26'  : range(508, 508+1), # 508:508
  'enMonitorAdc_26' : range(509, 509+1), # 509:509
  'ampToBus_26'     : range(510, 510+1), # 510:510
  'enAmpP_26'       : range(511, 511+1), # 511:511
  'frontEndSelNP_26': range(512, 512+1), # 512:512
  'enAmpN_26'       : range(513, 513+1), # 513:513

  'baselineTrimP_27': range(515, 521+1), # 521:515
  'enSignalAdc_27'  : range(522, 522+1), # 522:522
  'enMonitorAdc_27' : range(523, 523+1), # 523:523
  'ampToBus_27'     : range(524, 524+1), # 524:524
  'enAmpP_27'       : range(525, 525+1), # 525:525
  'frontEndSelNP_27': range(526, 526+1), # 526:526
  'enAmpN_27'       : range(527, 527+1), # 527:527

  'baselineTrimP_28': range(529, 535+1), # 535:529
  'enSignalAdc_28'  : range(536, 536+1), # 536:536
  'enMonitorAdc_28' : range(537, 537+1), # 537:537
  'ampToBus_28'     : range(538, 538+1), # 538:538
  'enAmpP_28'       : range(539, 539+1), # 539:539
  'frontEndSelNP_28': range(540, 540+1), # 540:540
  'enAmpN_28'       : range(541, 541+1), # 541:541

  'baselineTrimP_29': range(543, 549+1), # 549:543
  'enSignalAdc_29'  : range(550, 550+1), # 550:550
  'enMonitorAdc_29' : range(551, 551+1), # 551:551
  'ampToBus_29'     : range(552, 552+1), # 552:552
  'enAmpP_29'       : range(553, 553+1), # 553:553
  'frontEndSelNP_29': range(554, 554+1), # 554:554
  'enAmpN_29'       : range(555, 555+1), # 555:555

  'baselineTrimP_30': range(557, 563+1), # 563:557
  'enSignalAdc_30'  : range(564, 564+1), # 564:564
  'enMonitorAdc_30' : range(565, 565+1), # 565:565
  'ampToBus_30'     : range(566, 566+1), # 566:566
  'enAmpP_30'       : range(567, 567+1), # 567:567
  'frontEndSelNP_30': range(568, 568+1), # 568:568
  'enAmpN_30'       : range(569, 569+1), # 569:569

  'baselineTrimP_31': range(571, 577+1), # 577:571
  'enSignalAdc_31'  : range(578, 578+1), # 578:578
  'enMonitorAdc_31' : range(579, 579+1), # 579:579
  'ampToBus_31'     : range(580, 580+1), # 580:580
  'enAmpP_31'       : range(581, 581+1), # 581:581
  'frontEndSelNP_31': range(582, 582+1), # 582:582
  'enAmpN_31'       : range(583, 583+1), # 583:583
}

#--------------------------------------------------------------------
# inherit the generic shift register class
#--------------------------------------------------------------------
SR_READ  = 1
SR_WRITE = 2

class SpadicShiftRegister(ShiftRegister):
    """Representation of the SPADIC shift register."""
    def __init__(self, spadic):
        self._write_register = spadic.write_register
        self._read_register = spadic.read_register
        ShiftRegister.__init__(self, SPADIC_SR_LENGTH, SPADIC_SR)

    def _write(self, bits):
        """Perform the write operation of the whole shift register."""
        ctrl_data = (self._length << 3) + SR_WRITE
        self._write_register(0x2F0, ctrl_data)

        # divide bit string into 16 bit chunks (LSB first)
        while bits:
            chunk = bits[-16:] # take the last 16 bits
            bits  = bits[:-16] # remove the last 16 bits
            self._write_register(0x300, int(chunk, 2))

    def _read(self):
        """Perform the write operation of the whole shift register."""
        ctrl_data = (self._length << 3) + SR_READ
        self._write_register(0x2F0, ctrl_data)

        # read 16 bit chunks and concatenate (LSB first)
        bits = ''
        bits_left = self._length
        while bits_left:
            len_chunk = min(bits_left, 16)
            chunk = int2bitstring(self._read_register(0x300), len_chunk)
            bits = chunk + bits
            bits_left -= len_chunk
        return bits


from collections.abc import Mapping

from .registerfile import RegisterReadFailure

# In this module, the "binary representation" of an n-bit number will be a
# string of '0' and '1' characters, with the MSB at position 0 (to the
# left) and the LSB at position n-1 (to the right).
# This convention is chosen such that a printed bit string can be read
# normally and can be converted to a number by "int(bitstring, 2)". It
# contrasts, however, with the convention that "bitstring[0]" is be the
# LSB and "bitstring[n-1]" is the MSB, which is used in Verilog.

def int2bitstring(x, n):
    """Convert an integer to its binary representation.

    The result is a string of (enforced) length n with the MSB at position
    0 (left) and the LSB at position n-1 (right), so that "int(result, 2)"
    reverses the operation (if n was chosen large enough...).

    Example:
      int2bitstring(5, 8) -> '00000101'
      int('00000101', 2) -> 5
    """
    x += 2**n                # support two's complement
    s = bin(x)[2:]           # remove '0b' at the beginning
    s = s.rjust(n, '0')[-n:] # make string of length n
    return ''.join(s)


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


    # The following methods are there for providing the same interface as
    # the Register class from registerfile.py. They allow faking a
    # ShiftRegister with a RegisterFile, as done in SpadicControlClient.
    def apply(self):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

    def write(self, value):
        """
        Modify the register value, if necessary perform the write operation.
        
        Has the same effect as calling "set" and then "apply".
        """
        self.set(value)
        self.apply()

    def read(self):
        """
        Return the register value, if necessary perform the read operation.
        
        Has the same effect as calling "update" and then "get".
        """
        self.update()
        return self.get()


class ShiftRegister(Mapping):
    """Representation of a generic shift register."""

    def __init__(self, length, register_map):
        """Set up all registers."""
        self._length = length

        self._registers = {}
        for (name, positions) in register_map.items():
            r = ShiftRegisterEntry(positions)
            r.update = self.update
            r.apply = self.apply
            self._registers[name] = r

        self._last_bits = None
        self._known = False

    # collections.abc.Mapping provides __contains__, keys, items, values, get,
    # __eq__, and __ne__
    def __getitem__(self, key):
        return self._registers.__getitem__(key)

    def __iter__(self):
        return self._registers.__iter__()

    def __len__(self):
        return self._registers.__len__()


    def _write(self, bits):
        raise NotImplementedError(
            "Overwrite this with the hardware write operation.")

    def _read(self):
        raise NotImplementedError(
            "Overwrite this with the hardware read operation.")


    def _to_bits(self):
        """Generate bit string from configuration."""
        # Not all bit positions are necessarily used and the unused bits
        # are not necessarily 0. Therefore, before we have written
        # something, comparing self._to_bits() with self._last_bits like in
        # self.update(), may result in False, even though the bits used
        # for the configuration are equal. A possible solution is to use
        # _last_bits instead of all 0's as initial bit string. A possible
        # disadvantage of this is that the unused bits will never be
        # cleared.
        if self._last_bits:
            bits = [b for b in self._last_bits]
        else:
            bits = ['0']*self._length
        #bits = ['0']*self._length
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
            value = int(''.join(value_bits), 2)
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
# name              : [MSB, ..., LSB]

  'VNDel'           : list(range(  1,   7+1)),
  'VPDel'           : list(range(  9,  15+1)),
  'VPLoadFB2'       : list(range( 17,  23+1)),
  'VPLoadFB'        : list(range( 25,  31+1)),
  'VPFB'            : list(range( 33,  39+1)),
  'VPAmp'           : list(range( 41,  47+1)),
  'baselineTrimN'   : list(range( 49,  55+1)),

  'DecSelectNP'     : list(range( 56,  56+1)),
  'pCascP'          : list(range( 57,  63+1)),
  'SelMonitor'      : list(range( 64,  64+1)),
  'nCascP'          : list(range( 65,  71+1)),
  'pSourceBiasN'    : list(range( 73,  79+1)),
  'pSourceBiasP'    : list(range( 81,  87+1)),
  'nSourceBiasN'    : list(range( 89,  95+1)),
  'nSourceBiasP'    : list(range( 97, 103+1)),
  'pFBN'            : list(range(105, 111+1)),
  'nFBP'            : list(range(113, 119+1)),
  'pCascN'          : list(range(121, 127+1)),
  'nCascN'          : list(range(129, 135+1)),

  'baselineTrimP_0' : list(range(137, 143+1)),
  'enSignalAdc_0'   : list(range(144, 144+1)),
  'enMonitorAdc_0'  : list(range(145, 145+1)),
  'ampToBus_0'      : list(range(146, 146+1)),
  'enAmpP_0'        : list(range(147, 147+1)),
  'frontEndSelNP_0' : list(range(148, 148+1)),
  'enAmpN_0'        : list(range(149, 149+1)),

  'baselineTrimP_1' : list(range(151, 157+1)),
  'enSignalAdc_1'   : list(range(158, 158+1)),
  'enMonitorAdc_1'  : list(range(159, 159+1)),
  'ampToBus_1'      : list(range(160, 160+1)),
  'enAmpP_1'        : list(range(161, 161+1)),
  'frontEndSelNP_1' : list(range(162, 162+1)),
  'enAmpN_1'        : list(range(163, 163+1)),

  'baselineTrimP_2' : list(range(165, 171+1)),
  'enSignalAdc_2'   : list(range(172, 172+1)),
  'enMonitorAdc_2'  : list(range(173, 173+1)),
  'ampToBus_2'      : list(range(174, 174+1)),
  'enAmpP_2'        : list(range(175, 175+1)),
  'frontEndSelNP_2' : list(range(176, 176+1)),
  'enAmpN_2'        : list(range(177, 177+1)),

  'baselineTrimP_3' : list(range(179, 185+1)),
  'enSignalAdc_3'   : list(range(186, 186+1)),
  'enMonitorAdc_3'  : list(range(187, 187+1)),
  'ampToBus_3'      : list(range(188, 188+1)),
  'enAmpP_3'        : list(range(189, 189+1)),
  'frontEndSelNP_3' : list(range(190, 190+1)),
  'enAmpN_3'        : list(range(191, 191+1)),

  'baselineTrimP_4' : list(range(193, 199+1)),
  'enSignalAdc_4'   : list(range(200, 200+1)),
  'enMonitorAdc_4'  : list(range(201, 201+1)),
  'ampToBus_4'      : list(range(202, 202+1)),
  'enAmpP_4'        : list(range(203, 203+1)),
  'frontEndSelNP_4' : list(range(204, 204+1)),
  'enAmpN_4'        : list(range(205, 205+1)),

  'baselineTrimP_5' : list(range(207, 213+1)),
  'enSignalAdc_5'   : list(range(214, 214+1)),
  'enMonitorAdc_5'  : list(range(215, 215+1)),
  'ampToBus_5'      : list(range(216, 216+1)),
  'enAmpP_5'        : list(range(217, 217+1)),
  'frontEndSelNP_5' : list(range(218, 218+1)),
  'enAmpN_5'        : list(range(219, 219+1)),

  'baselineTrimP_6' : list(range(221, 227+1)),
  'enSignalAdc_6'   : list(range(228, 228+1)),
  'enMonitorAdc_6'  : list(range(229, 229+1)),
  'ampToBus_6'      : list(range(230, 230+1)),
  'enAmpP_6'        : list(range(231, 231+1)),
  'frontEndSelNP_6' : list(range(232, 232+1)),
  'enAmpN_6'        : list(range(233, 233+1)),

  'baselineTrimP_7' : list(range(235, 241+1)),
  'enSignalAdc_7'   : list(range(242, 242+1)),
  'enMonitorAdc_7'  : list(range(243, 243+1)),
  'ampToBus_7'      : list(range(244, 244+1)),
  'enAmpP_7'        : list(range(245, 245+1)),
  'frontEndSelNP_7' : list(range(246, 246+1)),
  'enAmpN_7'        : list(range(247, 247+1)),

  'baselineTrimP_8' : list(range(249, 255+1)),
  'enSignalAdc_8'   : list(range(256, 256+1)),
  'enMonitorAdc_8'  : list(range(257, 257+1)),
  'ampToBus_8'      : list(range(258, 258+1)),
  'enAmpP_8'        : list(range(259, 259+1)),
  'frontEndSelNP_8' : list(range(260, 260+1)),
  'enAmpN_8'        : list(range(261, 261+1)),

  'baselineTrimP_9' : list(range(263, 269+1)),
  'enSignalAdc_9'   : list(range(270, 270+1)),
  'enMonitorAdc_9'  : list(range(271, 271+1)),
  'ampToBus_9'      : list(range(272, 272+1)),
  'enAmpP_9'        : list(range(273, 273+1)),
  'frontEndSelNP_9' : list(range(274, 274+1)),
  'enAmpN_9'        : list(range(275, 275+1)),

  'baselineTrimP_10': list(range(277, 283+1)),
  'enSignalAdc_10'  : list(range(284, 284+1)),
  'enMonitorAdc_10' : list(range(285, 285+1)),
  'ampToBus_10'     : list(range(286, 286+1)),
  'enAmpP_10'       : list(range(287, 287+1)),
  'frontEndSelNP_10': list(range(288, 288+1)),
  'enAmpN_10'       : list(range(289, 289+1)),

  'baselineTrimP_11': list(range(291, 297+1)),
  'enSignalAdc_11'  : list(range(298, 298+1)),
  'enMonitorAdc_11' : list(range(299, 299+1)),
  'ampToBus_11'     : list(range(300, 300+1)),
  'enAmpP_11'       : list(range(301, 301+1)),
  'frontEndSelNP_11': list(range(302, 302+1)),
  'enAmpN_11'       : list(range(303, 303+1)),

  'baselineTrimP_12': list(range(305, 311+1)),
  'enSignalAdc_12'  : list(range(312, 312+1)),
  'enMonitorAdc_12' : list(range(313, 313+1)),
  'ampToBus_12'     : list(range(314, 314+1)),
  'enAmpP_12'       : list(range(315, 315+1)),
  'frontEndSelNP_12': list(range(316, 316+1)),
  'enAmpN_12'       : list(range(317, 317+1)),

  'baselineTrimP_13': list(range(319, 325+1)),
  'enSignalAdc_13'  : list(range(326, 326+1)),
  'enMonitorAdc_13' : list(range(327, 327+1)),
  'ampToBus_13'     : list(range(328, 328+1)),
  'enAmpP_13'       : list(range(329, 329+1)),
  'frontEndSelNP_13': list(range(330, 330+1)),
  'enAmpN_13'       : list(range(331, 331+1)),

  'baselineTrimP_14': list(range(333, 339+1)),
  'enSignalAdc_14'  : list(range(340, 340+1)),
  'enMonitorAdc_14' : list(range(341, 341+1)),
  'ampToBus_14'     : list(range(342, 342+1)),
  'enAmpP_14'       : list(range(343, 343+1)),
  'frontEndSelNP_14': list(range(344, 344+1)),
  'enAmpN_14'       : list(range(345, 345+1)),

  'baselineTrimP_15': list(range(347, 353+1)),
  'enSignalAdc_15'  : list(range(354, 354+1)),
  'enMonitorAdc_15' : list(range(355, 355+1)),
  'ampToBus_15'     : list(range(356, 356+1)),
  'enAmpP_15'       : list(range(357, 357+1)),
  'frontEndSelNP_15': list(range(358, 358+1)),
  'enAmpN_15'       : list(range(359, 359+1)),

  'baselineTrimP_16': list(range(361, 367+1)),
  'enSignalAdc_16'  : list(range(368, 368+1)),
  'enMonitorAdc_16' : list(range(369, 369+1)),
  'ampToBus_16'     : list(range(370, 370+1)),
  'enAmpP_16'       : list(range(371, 371+1)),
  'frontEndSelNP_16': list(range(372, 372+1)),
  'enAmpN_16'       : list(range(373, 373+1)),

  'baselineTrimP_17': list(range(375, 381+1)),
  'enSignalAdc_17'  : list(range(382, 382+1)),
  'enMonitorAdc_17' : list(range(383, 383+1)),
  'ampToBus_17'     : list(range(384, 384+1)),
  'enAmpP_17'       : list(range(385, 385+1)),
  'frontEndSelNP_17': list(range(386, 386+1)),
  'enAmpN_17'       : list(range(387, 387+1)),

  'baselineTrimP_18': list(range(389, 395+1)),
  'enSignalAdc_18'  : list(range(396, 396+1)),
  'enMonitorAdc_18' : list(range(397, 397+1)),
  'ampToBus_18'     : list(range(398, 398+1)),
  'enAmpP_18'       : list(range(399, 399+1)),
  'frontEndSelNP_18': list(range(400, 400+1)),
  'enAmpN_18'       : list(range(401, 401+1)),

  'baselineTrimP_19': list(range(403, 409+1)),
  'enSignalAdc_19'  : list(range(410, 410+1)),
  'enMonitorAdc_19' : list(range(411, 411+1)),
  'ampToBus_19'     : list(range(412, 412+1)),
  'enAmpP_19'       : list(range(413, 413+1)),
  'frontEndSelNP_19': list(range(414, 414+1)),
  'enAmpN_19'       : list(range(415, 415+1)),

  'baselineTrimP_20': list(range(417, 423+1)),
  'enSignalAdc_20'  : list(range(424, 424+1)),
  'enMonitorAdc_20' : list(range(425, 425+1)),
  'ampToBus_20'     : list(range(426, 426+1)),
  'enAmpP_20'       : list(range(427, 427+1)),
  'frontEndSelNP_20': list(range(428, 428+1)),
  'enAmpN_20'       : list(range(429, 429+1)),

  'baselineTrimP_21': list(range(431, 437+1)),
  'enSignalAdc_21'  : list(range(438, 438+1)),
  'enMonitorAdc_21' : list(range(439, 439+1)),
  'ampToBus_21'     : list(range(440, 440+1)),
  'enAmpP_21'       : list(range(441, 441+1)),
  'frontEndSelNP_21': list(range(442, 442+1)),
  'enAmpN_21'       : list(range(443, 443+1)),

  'baselineTrimP_22': list(range(445, 451+1)),
  'enSignalAdc_22'  : list(range(452, 452+1)),
  'enMonitorAdc_22' : list(range(453, 453+1)),
  'ampToBus_22'     : list(range(454, 454+1)),
  'enAmpP_22'       : list(range(455, 455+1)),
  'frontEndSelNP_22': list(range(456, 456+1)),
  'enAmpN_22'       : list(range(457, 457+1)),

  'baselineTrimP_23': list(range(459, 465+1)),
  'enSignalAdc_23'  : list(range(466, 466+1)),
  'enMonitorAdc_23' : list(range(467, 467+1)),
  'ampToBus_23'     : list(range(468, 468+1)),
  'enAmpP_23'       : list(range(469, 469+1)),
  'frontEndSelNP_23': list(range(470, 470+1)),
  'enAmpN_23'       : list(range(471, 471+1)),

  'baselineTrimP_24': list(range(473, 479+1)),
  'enSignalAdc_24'  : list(range(480, 480+1)),
  'enMonitorAdc_24' : list(range(481, 481+1)),
  'ampToBus_24'     : list(range(482, 482+1)),
  'enAmpP_24'       : list(range(483, 483+1)),
  'frontEndSelNP_24': list(range(484, 484+1)),
  'enAmpN_24'       : list(range(485, 485+1)),

  'baselineTrimP_25': list(range(487, 493+1)),
  'enSignalAdc_25'  : list(range(494, 494+1)),
  'enMonitorAdc_25' : list(range(495, 495+1)),
  'ampToBus_25'     : list(range(496, 496+1)),
  'enAmpP_25'       : list(range(497, 497+1)),
  'frontEndSelNP_25': list(range(498, 498+1)),
  'enAmpN_25'       : list(range(499, 499+1)),

  'baselineTrimP_26': list(range(501, 507+1)),
  'enSignalAdc_26'  : list(range(508, 508+1)),
  'enMonitorAdc_26' : list(range(509, 509+1)),
  'ampToBus_26'     : list(range(510, 510+1)),
  'enAmpP_26'       : list(range(511, 511+1)),
  'frontEndSelNP_26': list(range(512, 512+1)),
  'enAmpN_26'       : list(range(513, 513+1)),

  'baselineTrimP_27': list(range(515, 521+1)),
  'enSignalAdc_27'  : list(range(522, 522+1)),
  'enMonitorAdc_27' : list(range(523, 523+1)),
  'ampToBus_27'     : list(range(524, 524+1)),
  'enAmpP_27'       : list(range(525, 525+1)),
  'frontEndSelNP_27': list(range(526, 526+1)),
  'enAmpN_27'       : list(range(527, 527+1)),

  'baselineTrimP_28': list(range(529, 535+1)),
  'enSignalAdc_28'  : list(range(536, 536+1)),
  'enMonitorAdc_28' : list(range(537, 537+1)),
  'ampToBus_28'     : list(range(538, 538+1)),
  'enAmpP_28'       : list(range(539, 539+1)),
  'frontEndSelNP_28': list(range(540, 540+1)),
  'enAmpN_28'       : list(range(541, 541+1)),

  'baselineTrimP_29': list(range(543, 549+1)),
  'enSignalAdc_29'  : list(range(550, 550+1)),
  'enMonitorAdc_29' : list(range(551, 551+1)),
  'ampToBus_29'     : list(range(552, 552+1)),
  'enAmpP_29'       : list(range(553, 553+1)),
  'frontEndSelNP_29': list(range(554, 554+1)),
  'enAmpN_29'       : list(range(555, 555+1)),

  'baselineTrimP_30': list(range(557, 563+1)),
  'enSignalAdc_30'  : list(range(564, 564+1)),
  'enMonitorAdc_30' : list(range(565, 565+1)),
  'ampToBus_30'     : list(range(566, 566+1)),
  'enAmpP_30'       : list(range(567, 567+1)),
  'frontEndSelNP_30': list(range(568, 568+1)),
  'enAmpN_30'       : list(range(569, 569+1)),

  'baselineTrimP_31': list(range(571, 577+1)),
  'enSignalAdc_31'  : list(range(578, 578+1)),
  'enMonitorAdc_31' : list(range(579, 579+1)),
  'ampToBus_31'     : list(range(580, 580+1)),
  'enAmpP_31'       : list(range(581, 581+1)),
  'frontEndSelNP_31': list(range(582, 582+1)),
  'enAmpN_31'       : list(range(583, 583+1)),
}

#--------------------------------------------------------------------
# inherit the generic shift register class
#--------------------------------------------------------------------
SR_READ  = 1
SR_WRITE = 2

ADDR_CTRL = 0x6a << 3  # SPADIC 1.x: 0x2f0
ADDR_DATA = 0x6c << 3  # SPADIC 1.x: 0x300

CHUNK_SIZE = 15        # SPADIC 1.x: 16

class ShiftRegisterReadFailure(Exception):
    pass

class SpadicShiftRegister(ShiftRegister):
    """Representation of the SPADIC shift register."""
    def __init__(self, write_registers, read_registers):
        self._write_registers = write_registers
        self._read_registers = read_registers
        ShiftRegister.__init__(self, SPADIC_SR_LENGTH, SPADIC_SR)

    def _write(self, bits):
        """Perform the write operation of the whole shift register."""
        ctrl_data = (self._length << 3) + SR_WRITE
        self._write_registers([(ADDR_CTRL, ctrl_data)])

        # divide bit string into chunks, right first
        while bits:
            chunk = bits[-CHUNK_SIZE:] # take the last bits
            bits  = bits[:-CHUNK_SIZE] # remove the last bits
            # one chunk is written LSB first (from "shift.v"):
            #   sr_write_bitin <= write_buf[0];
            #   write_buf[14:0] <= write_buf[15:1];
            self._write_registers([(ADDR_DATA, int(chunk, 2))])

    def _read(self):
        """Perform the read operation of the whole shift register.

        Calls _read_once until it succeeds.
        """
        while True:
            try:
                return self._read_once()
            except ShiftRegisterReadFailure:
                continue

    def _read_once(self):
        """Read the whole shift register once.

        May fail, raise ShiftRegisterReadFailure in that case.
        """
        ctrl_data = (self._length << 3) + SR_READ
        self._write_registers([(ADDR_CTRL, ctrl_data)])

        # collect needed read requests for chunks with given size
        bits_left = self._length
        chunks = []
        while bits_left:
            len_chunk = min(bits_left, CHUNK_SIZE)
            chunks.append(len_chunk)
            bits_left -= len_chunk

        # read chunks
        try:
            result = self._read_registers([ADDR_DATA for c in chunks],
                                          attempt_alignment=False)
        except RegisterReadFailure:
            raise ShiftRegisterReadFailure

        # concatenate chunks, right first
        bits = ''
        for len_chunk, chunk in zip(chunks, result):
            # one chunk is read MSB first (from "shift.v"):
            #   read_buf <= {read_buf[14:0],sr_read_bitout};
            # so we have to reverse the bit order again
            chunk_bits = ''.join(reversed(int2bitstring(chunk, len_chunk)))
            bits = chunk_bits + bits
        return bits

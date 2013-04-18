def match_word(word, (value, mask)):
    """Test if a part of a word matches a given value."""
    return word & mask == value


#--------------------------------------------------------------------
# preambles (value, mask)
#--------------------------------------------------------------------
preamble = {
  'wSOM': (0x8000, 0xF000), # start of message
  'wTSW': (0x9000, 0xF000), # time stamp
  'wRDA': (0xA000, 0xF000), # raw data
  'wEOM': (0xB000, 0xF000), # end of data message
  'wBOM': (0xC000, 0xF000), # buffer overflow counter, end of message
  'wEPM': (0xD000, 0xF000), # epoch marker, end of message 
  'wEXD': (0xE000, 0xF000), # extracted data 
  'wINF': (0xF000, 0xF000), # information 
  'wCON': (0x0000, 0x8000)  # continuation preamble
}

#--------------------------------------------------------------------
# stop types (value, mask)
#--------------------------------------------------------------------
stoptype = {
  'sEND': (0x0000, 0x0007),
  'sEBF': (0x0001, 0x0007),
  'sEFF': (0x0002, 0x0007),
  'sEDH': (0x0003, 0x0007),
  'sEDB': (0x0004, 0x0007),
  'sEDO': (0x0005, 0x0007),
  'sXX1': (0x0006, 0x0007), # unused
  'sXX2': (0x0007, 0x0007)  # unused
}
stoptype_str = {
  0: 'normal end of message',
  1: 'channel buffer full',
  2: 'ordering fifo full',
  3: 'multi hit',
  4: 'multi hit and channel buffer full',
  5: 'multi hit and ordering fifo full'
}

#--------------------------------------------------------------------
# info types (value, mask)
#--------------------------------------------------------------------
infotype = {
  'iDIS': (0x0000, 0x0F00),
  'iNGT': (0x0100, 0x0F00),
  'iNRT': (0x0200, 0x0F00),
  'iNBE': (0x0300, 0x0F00),
  'iMSB': (0x0400, 0x0F00),
  'iNOP': (0x0500, 0x0F00),
  'iSYN': (0x0600, 0x0F00),
  'iXX3': (0x0700, 0x0F00), # unused
  'iXX4': (0x0800, 0x0F00), # unused
  'iXX5': (0x0900, 0x0F00), # unused
  'iXX6': (0x0A00, 0x0F00), # unused
  'iXX7': (0x0B00, 0x0F00), # unused
  'iXX8': (0x0C00, 0x0F00), # unused
  'iXX9': (0x0D00, 0x0F00), # unused
  'iXXA': (0x0E00, 0x0F00), # unused
  'iXXB': (0x0F00, 0x0F00)  # unused
}
infotype_str = {
  0: 'disable channel during message readout',
  1: 'next grant timeout',
  2: 'next request timeout',
  3: 'new grant but channel empty',
  4: 'corruption in message builder',
  5: 'empty word',
  6: 'out of sync'
}

#--------------------------------------------------------------------
# hit types (value, mask)
#--------------------------------------------------------------------
hittype = {
  'hGLB': (0x0000, 0x0030),
  'hSLF': (0x0010, 0x0030),
  'hNBR': (0x0020, 0x0030),
  'hSAN': (0x0030, 0x0030) 
}
hittype_str = {
  0: 'global trigger',
  1: 'self triggered',
  2: 'neighbor triggered',
  3: 'self and neighbor triggered'
}



#====================================================================
# message reconstruction & interpretation
#====================================================================

#--------------------------------------------------------------------
# split sequence of message words into messages (or info words)
#--------------------------------------------------------------------
class MessageSplitter:
    """Splits a stream of message words into individual messages."""
    def __init__(self):
        self._remainder = []

    def __call__(self, message_words):
        """Feed new message words."""
        # recall remainder from the last time
        message = self._remainder

        for w in message_words:
            # first check if info word and discard NOP words
            if match_word(w, preamble['wINF']):
                if not match_word(w, infotype['iNOP']):
                    yield [w]
                    message = []
                continue
            # start new message at start of message marker
            elif match_word(w, preamble['wSOM']):
                message = []

            # build up message
            message.append(w)

            # yield message at all possible end of message markers
            # also clear it so it is not stored as remainder
            if any(match_word(w, preamble[p])
                   for p in ['wEOM', 'wBOM', 'wEPM']):
                yield message
                message = []

        # store remainder for the next time
        self._remainder = message


#--------------------------------------------------------------------
# extract information from messages
#--------------------------------------------------------------------
class Message():
    """Representation of a SPADIC 1.0 message."""

    def __init__(self, words):
        """Extract the metadata from the message."""
        self.group_id              = None
        self.channel_id            = None
        self.timestamp             = None
        self._data                 = None
        self.num_data              = None
        self.hit_type              = None
        self.stop_type             = None
        self.buffer_overflow_count = None
        self.epoch_count           = None
        self.info_type             = None

        self.words = words

        for w in words:
            # start of message -> group ID, channel IDs
            if match_word(w, preamble['wSOM']):
                self.group_id   = (w & 0x0FF0) >> 4
                self.channel_id = (w & 0x000F)

            # timestamp
            elif match_word(w, preamble['wTSW']):
                self.timestamp = (w & 0x0FFF)

            # end of message -> num. data, hit type, stop type
            elif match_word(w, preamble['wEOM']):
                self.num_data = (w & 0x0FC0) >> 6
                self.hit_type = (w & 0x0030) >> 4
                self.stop_type = (w & 0x0007)

            # buffer overflow count
            elif match_word(w, preamble['wBOM']):
                self.buffer_overflow_count = (w & 0x00FF)

            # epoch marker
            elif match_word(w, preamble['wEPM']):
                self.epoch_count = (w & 0x0FFF)

            # info words
            elif match_word(w, preamble['wINF']):
                self.info_type = (w & 0x0F00) >> 8
                if any(match_word(w, infotype[it])
                       for it in ['iDIS', 'iNGT', 'iNBE', 'iMSB']):
                    self.channel_id = (w & 0x00F0) >> 4
                elif match_word(w, infotype['iSYN']):
                    self.epoch_count = (w & 0x00FF)


    def _update_data(self):
        """Extract the data samples from the message."""
        def iter_data():
            r = 0 # data buffer
            pos = -9 # initial position of the mask LSB
            for w in self.words:
                if pos < 0:
                    if match_word(w, preamble['wRDA']):
                        r = (r << 12) + (w & 0x0FFF)
                        pos += 12
                    elif match_word(w, preamble['wCON']):
                        r = (r << 15) + (w & 0x7FFF)
                        pos += 15

                while pos >= 0:
                    mask = 0x1FF << pos
                    yield (r & mask) >> pos
                    r = (r & ~mask)
                    pos -= 9

        data = [x-512 if x > 255 else x
                for x in iter_data()]
        self._data = data[:self.num_data]


    def data(self):
        """Get the data samples."""
        if self._data is None:
            self._update_data()
        return self._data
                

    def report(self, verbose=False):
        """Make a human-readable report."""
        self._update_data()
        s = []

        if verbose:
            s.append('\n'.join('%3i: %04X' % (i, word)
                               for (i, word) in enumerate(self.words)))

        if self.group_id is not None:
            s.append('group: %i' % self.group_id)
        if self.channel_id is not None:
            s.append('channel: %i' % self.channel_id)
        if self.timestamp is not None:
            s.append('timestamp: %i' % self.timestamp)
        if self._data:
            s.append('data (%i values): ' % self.num_data +
                     ', '.join(str(x) for x in self._data))
        if self.hit_type is not None:
            s.append('hit type: %s' % hittype_str[self.hit_type])
        if self.stop_type is not None:
            s.append('stop type: %s' % stoptype_str[self.stop_type])
        if self.buffer_overflow_count is not None:
            s.append('buffer overflow count: %i' % self.buffer_overflow_count)
        if self.epoch_count is not None:
            s.append('epoch count: %i' % self.epoch_count)
        if self.info_type is not None:
            s.append('info type: %s' % infotype_str[self.info_type])

        return '\n'.join(s)


    def __str__(self):
        return self.report(verbose=True)


    # TODO move this somewhere else
    ##----------------------------------------------------------------
    ## return data points in a format suitable for gnuplot (x: time in ns)
    ##----------------------------------------------------------------
    #def data_gnuplot(self, mask='1'*32, T=40):
    #    if self.data is not None:
    #        t = [i*T for (i, m) in enumerate(mask) if m=='1']
    #        return'\n'.join('%5i %5i' % (x, y)
    #                        for (x, y) in zip(t, self.data))




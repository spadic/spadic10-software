from bit_byte_helper import int2bitstring


#====================================================================
# SPADIC message definitions
#====================================================================

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
# end of message types
#--------------------------------------------------------------------
endofmessage = {
  'eEND': (0x0000, 0x0007),
  'eEBF': (0x0001, 0x0007),
  'eEFF': (0x0002, 0x0007),
  'eEDH': (0x0003, 0x0007),
  'eEDB': (0x0004, 0x0007),
  'eEDO': (0x0005, 0x0007),
  'eXX1': (0x0006, 0x0007), # unused
  'eXX2': (0x0007, 0x0007)  # unused
}
endofmessage_str = {
  'eEND': 'normal end of message',
  'eEBF': 'buffer full',
  'eEFF': 'ordering fifo full',
  'eEDH': 'multi hit',
  'eEDB': 'multi hit but buffer full',
  'eEDO': 'multi hit but ordering fifo full'
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
  'iDIS': 'disable channel during message readout',
  'iNGT': 'next grant timeout',
  'iNRT': 'next request timeout',
  'iNBE': 'new grant but channel empty',
  'iMSB': 'corruption in message builder',
  'iNOP': 'empty word',
  'iSYN': 'out of sync'
}

#--------------------------------------------------------------------
# hit types
#--------------------------------------------------------------------
hittype = {
  'eNON': (0x0000, 0x0030),
  'eINT': (0x0010, 0x0030),
  'eEXT': (0x0020, 0x0030),
  'eIAE': (0x0030, 0x0030) 
}
hittype_str = {
  'eNON': 'no hit, error',
  'eINT': 'internal hit',
  'eEXT': 'external hit',
  'eIAE': 'int+ext hit'
}



#====================================================================
# message reconstruction & interpretation
#====================================================================

def match_word(word, (value, mask)):
    return word & mask == value

#--------------------------------------------------------------------
# split sequence of message words into messages (or info words)
#--------------------------------------------------------------------
class MessageSplitter:
    def __init__(self):
        self._remainder = []

    def __call__(self, message_words):
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
# Message class
#--------------------------------------------------------------------
class Message():
    group_id              = None
    channel_id            = None
    timestamp             = None
    data                  = None
    num_data              = None
    hit_type              = None
    stop_type             = None
    buffer_overflow_count = None
    epoch_count           = None
    info_type             = None
    _valid                = True

    def __init__(self, message): # message = output of messages()
        self.words = message     # i.e. some raw 16-bit words

        #------------------------------------------------------------
        # get start of message (group/channel IDs)
        #------------------------------------------------------------
        start_words = [word for word in message
                       if word.startswith(preamble['wSOM'])]
        if start_words:
            w = start_words[0]
            self.group_id   = int(w[4:12], 2)
            self.channel_id = int(w[12:16], 2)

        #------------------------------------------------------------
        # get timestamp
        #------------------------------------------------------------
        timestamp_words = [word for word in message
                           if word.startswith(preamble['wTSW'])]
        if timestamp_words:
            w = timestamp_words[0]
            self.timestamp = int(w[len(preamble['wTSW']):], 2)

        #------------------------------------------------------------
        # get raw data
        #------------------------------------------------------------
        rda_pos = [i for (i, word) in enumerate(message)
                   if word.startswith(preamble['wRDA'])]

        if rda_pos:
            p = rda_pos[0]

            # data begins with the rest of the 'start of raw data' word
            data_string = message[p][len(preamble['wRDA']):]

            # data continues for all consecutive words with continuation marker
            for word in message[p+1:]:
                if word.startswith(preamble['wCON']):
                    data_string += word[len(preamble['wCON']):]
                else:
                    break

            # split data in 9 bit values and interpret as 2-s complement
            self.data = [x-512 if x > 255 else x
                         for x in [int(data_string[i*9:(i+1)*9], 2)
                                   for i in range(len(data_string)/9)]]

        #------------------------------------------------------------
        # get end of message
        #------------------------------------------------------------
        end_words = [word for word in message
                     if any(word.startswith(preamble[p])
                            for p in ['wEOM', 'wBOM', 'wEPM'])]

        if end_words:
            w = end_words[0]

            # extract information for different cases
            if w.startswith(preamble['wEOM']):
                self.num_data = int(w[4:10], 2)
                if self.data is not None: # discard last 0 value
                    self.data = self.data[:self.num_data]
                try:
                    self.hit_type = hittype_str[w[10:12]]
                    self.stop_type = endofmessage_str[w[13:16]]
                except KeyError:
                    self._valid = False

            elif w.startswith(preamble['wBOM']):
                self.buffer_overflow_count = int(w[8:16], 2)

            elif w.startswith(preamble['wEPM']):
                self.epoch_count = int(w[4:16], 2)

        #------------------------------------------------------------
        # get info from info words
        #------------------------------------------------------------
        info_words = [word for word in message
                      if word.startswith(preamble['wINF'])]
        
        if info_words:
            w = info_words[0]
            try:
                self.info_type = infotype_str[w[4:8]]
            except KeyError:
                self._valid = False
            # channel_id only for some info types
            if w[4:8] in [infotype[t] for t in ['iDIS', 'iNGT']]:
                self.channel_id = int(word[8:12], 2)

        # end of __init__()

    #----------------------------------------------------------------
    # make human-readable report of a message
    #----------------------------------------------------------------
    def report(self, verbose=False):
        s = []
        if verbose:
            s.append('\n'.join('%3i: %s' % (i, word)
                               for (i, word) in enumerate(self.words)))

        if self.group_id is not None:
            s.append('group: %i' % self.group_id)
        if self.channel_id is not None:
            s.append('channel: %i' % self.channel_id)
        if self.timestamp is not None:
            s.append('timestamp: %i' % self.timestamp)
        if self.data is not None:
            s.append('data (%i values): ' % self.num_data +
                     ', '.join(str(x) for x in self.data))
        if self.hit_type is not None:
            s.append('hit type: %s' % self.hit_type)
        if self.stop_type is not None:
            s.append('stop type: %s' % self.stop_type)
        if self.buffer_overflow_count is not None:
            s.append('buffer overflow count: %i' % self.buffer_overflow_count)
        if self.epoch_count is not None:
            s.append('epoch count: %i' % self.epoch_count)
        if self.info_type is not None:
            s.append('info type: %s' % self.info_type)

        return '\n'.join(s)

    #----------------------------------------------------------------
    # 'print'ing a message returns verbose report
    #----------------------------------------------------------------
    def __str__(self):
        return self.report(verbose=True)

    #----------------------------------------------------------------
    # return data points in a format suitable for gnuplot (x: time in ns)
    #----------------------------------------------------------------
    def data_gnuplot(self, mask='1'*32, T=40):
        if self.data is not None:
            t = [i*T for (i, m) in enumerate(mask) if m=='1']
            return'\n'.join('%5i %5i' % (x, y)
                            for (x, y) in zip(t, self.data))




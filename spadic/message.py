from bit_byte_helper import int2bitstring


#====================================================================
# SPADIC message definitions
#====================================================================

#--------------------------------------------------------------------
# preambles 
#--------------------------------------------------------------------
preamble = {
  'wSOM': '1000', # start of message
  'wTSW': '1001', # time stamp
  'wRDA': '1010', # raw data
  'wEOM': '1011', # end of data message
  'wBOM': '1100', # buffer overflow counter, end of message
  'wEPM': '1101', # epoch marker, end of message 
  'wEXD': '1110', # extracted data 
  'wINF': '1111', # information 
  'wCON': '0'     # continuation preamble
}

#--------------------------------------------------------------------
# end of message types
#--------------------------------------------------------------------
endofmessage = {
  'eEND': '000', # normal end of message
  'eEBF': '001', # buffer full 
  'eEFF': '010', # ordering fifo full
  'eEDH': '011', # multi hit
  'eEDB': '100', # multi hit but buffer full
  'eEDO': '101', # multi hit but ordering fifo full
  'eXX1': '110', # unused
  'eXX2': '111'  # unused
}
endofmessage_str = {
  endofmessage['eEND']: 'normal end of message',
  endofmessage['eEBF']: 'buffer full',
  endofmessage['eEFF']: 'ordering fifo full',
  endofmessage['eEDH']: 'multi hit',
  endofmessage['eEDB']: 'multi hit but buffer full',
  endofmessage['eEDO']: 'multi hit but ordering fifo full'
}

#--------------------------------------------------------------------
# info types
#--------------------------------------------------------------------
infotype = {
  'iDIS': '0000', # corruption: disable channel during message readout, read from disabled channel
  'iNGT': '0001', # corruption: next grant timeout in switch, e.g. due to SEU
  'iNRT': '0010', # corruption: next request timeout in switch, e.g. due to SEU
  'iNBE': '0011', # corruption: new grant but channel empty in switch, e.g. due to SEU
  'iMSB': '0100', # corruption: corruption in message builder
  'iNOP': '0101', # empty word from cbm net wrapper, can be removed anytime
  'iSYN': '0110', # out of sync warning
  'iXX3': '0111', # unused
  'iXX4': '1000', # unused
  'iXX5': '1001', # unused
  'iXX6': '1010', # unused
  'iXX7': '1011', # unused
  'iXX8': '1100', # unused
  'iXX9': '1101', # unused
  'iXXA': '1110', # unused
  'iXXB': '1111'  # unused
}
infotype_str = {
  infotype['iDIS']: 'corruption: disable channel during message readout, read from disabled channel',
  infotype['iNGT']: 'corruption: next grant timeout in switch, e.g. due to SEU',
  infotype['iNRT']: 'corruption: next request timeout in switch, e.g. due to SEU',
  infotype['iNBE']: 'corruption: new grant but channel empty in switch, e.g. due to SEU',
  infotype['iMSB']: 'corruption: corruption in message builder',
  infotype['iNOP']: 'empty word from cbm net wrapper, can be removed anytime',
  infotype['iSYN']: 'out of sync warning'
}

#--------------------------------------------------------------------
# hit types
#--------------------------------------------------------------------
hittype = {
  'eNON': '00', # no hit, error
  'eINT': '01', # internal hit 
  'eEXT': '10', # external hit
  'eIAE': '11'  # int+ext hit
}
hittype_str = {
  hittype['eNON']: 'no hit, error',
  hittype['eINT']: 'internal hit',
  hittype['eEXT']: 'external hit',
  hittype['eIAE']: 'int+ext hit'
}



#====================================================================
# test data output reconstruction
#====================================================================

class _message_words:
    def __init__(self):
        self._sync = False
        self._remainder = [int2bitstring(0, 8)]*5 # at the time the first
                                        # pattern matching attempt is made,
                                        # the buffer must contain five bytes

    def __call__(self, byte_sequence): # byte_sequence must be an iterator
        # initialize buffer with the remainder from the last time
        buf = self._remainder

        # search for wSOM, wTSW and wRDA in successive 2-byte words:
        # [wSOM, ...] [wTSW, ...] [wRDA, ...
        #  0     1     2     3     4
        while not self._sync:
            # shift next byte into the buffer (must discard old bytes until
            # in sync, in order to guarantee that the very first word that
            # is yielded marks the beginning of a message)
            try:
                buf.append(int2bitstring(byte_sequence.next(), 8))
                buf = buf[1:] # do this after appending, so when
                              # StopIteration is raised, buf remains
                              # untouched
            except StopIteration:
                self._remainder = buf
                return
            # search the pattern in the newest five bytes
            self._sync = (buf[0].startswith(preamble['wSOM']) and
                          buf[2].startswith(preamble['wTSW']) and
                          buf[4].startswith(preamble['wRDA']))

        # once in sync, yield the oldest two bytes of the buffer
        for byte in byte_sequence:
            buf.append(int2bitstring(byte, 8))
            if len(buf) > 1:
                yield buf[0]+buf[1]
                buf = buf[2:]

        # store the remaining byte (if left over) for the next time
        self._remainder = buf

    def resync(self):
        self._sync = False
        self._remainder += [int2bitstring(0, 8)]*5


#====================================================================
# message reconstruction & interpretation
#====================================================================

#--------------------------------------------------------------------
# split sequence of message words into messages (or info words)
#--------------------------------------------------------------------
class _messages:
    def __init__(self):
        self._remainder = []

    def __call__(self, message_words):
        # recall remainder from the last time
        message = self._remainder

        for word in message_words:
            # start new message at start of message marker or info marker
            if any(word.startswith(preamble[p])
                   for p in ['wSOM', 'wINF']):
                message = []

            # build up message
            message.append(word)

            # yield message at all possible end of message markers
            # also clear it so it is not stored as remainder
            if any(word.startswith(preamble[p])
                   for p in ['wEOM', 'wBOM', 'wEPM', 'wINF']):
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
                self.hit_type = hittype_str[w[10:12]]
                self.stop_type = endofmessage_str[w[13:16]]

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
            self.info_type = infotype_str[w[4:8]]
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


#--------------------------------------------------------------------
# Message reader
#--------------------------------------------------------------------
class MessageReader:
    _read_words = _message_words()
    _read_messages = _messages()

    def __init__(self, spadic):
        self._spadic = spadic

    def read(self, num_bytes=None):
        d = self._spadic.read_data(num_bytes)
        w = self._read_words(d)
        m = self._read_messages(w)
        return [Message(mi) for mi in m]

    def resync(self):
        self._read_words.resync()


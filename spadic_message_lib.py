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
  endofmessage['eEBF']: 'buffer full ',
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
  hittype['eINT']: 'internal hit ',
  hittype['eEXT']: 'external hit',
  hittype['eIAE']: 'int+ext hit'
}

#--------------------------------------------------------------------
# selection mask
#--------------------------------------------------------------------
mask = '11111111111111111111111111111111'
#mask = '11110001111111111111111111111111'


#====================================================================
# message parser
#====================================================================

#-------------------------------------------------------------------------------
# read data words from simulation output file
#-------------------------------------------------------------------------------
def readSimOutputFile(filename):
    with open(filename) as f:
        for (i, line) in enumerate(f):
            yield (i, line.rstrip())


#-------------------------------------------------------------------------------
# split switch output data into info words and messages
#-------------------------------------------------------------------------------
def split_switch_output_data(switch_output_data):
    message = []

    for (i, word) in switchOutputData:
        if word.startswith(preamble['wSOM']):
            message = [(i, word)]

        elif any(word.startswith(preamble[p])
                 for p in ['wEOM', 'wBOM', 'wEPM', 'wINF']):
            message.append((i, word))
            yield message
            message = []

        else:
            message.append((i, word))


#-------------------------------------------------------------------------------
# get start of message (group/channel IDs)
#-------------------------------------------------------------------------------
def getGroupIdChannelId(message):
    start_words = [word for (i, word) in message
                   if word.startswith(preamble['wSOM'])]
    return [(int(word[4:12],2), int(word[12:16],2)) for word in start_words]
    #        groupID            channelID

    
#-------------------------------------------------------------------------------
# get timestamps
#-------------------------------------------------------------------------------
def getTimestamps(message):
    timestamp_words = [word for (i, word) in message
                       if word.startswith(preamble['wTSW'])]
    timestamps = [int(word[len(preamble['wTSW']):], 2)
                  for word in timestamp_words]
    return timestamps


#-------------------------------------------------------------------------------
# get raw data
#-------------------------------------------------------------------------------
def getRawData(message):
    RDA_positions = [j for (j, (i, word)) in enumerate(message)
                     if word.startswith(preamble['wRDA'])]
    rawdata_parts = []
    for RDA_position in RDA_positions:
        data_string = message[RDA_position][1][len(preamble['wRDA']):]
        for (i, word) in message[RDA_position+1:]:
            if word.startswith(preamble['wCON']):
                data_string += word[len(preamble['wCON']):]
            else:
                break
        data_values = [x-512 if x > 255 else x
                       for x in [int(data_string[i*9:(i+1)*9], 2)
                                 for i in range(len(data_string)/9)]]
        rawdata_parts.append(data_values)
    return rawdata_parts


#-------------------------------------------------------------------------------
# get end of message (end type, hit type, data length)
#-------------------------------------------------------------------------------
def getEndOfMessage(message):
    end_words = [word for (i, word) in message
                 if any(word.startswith(preamble[p])
                        for p in ['wEOM', 'wBOM', 'wEPM'])]
    eoms = []
    for end_word in end_words:
        if end_word.startswith(preamble['wEOM']):
            num_data = int(end_word[4:10], 2)
            hit_type = hittype_str[end_word[10:12]]
            end_reason = endofmessage_str[end_word[13:16]]
            
        elif end_word.startswith(preamble['wBOM']):
            buffer_overflow_counter = int(end_word[8:16], 2)
            num_data = buffer_overflow_counter
            hit_type = 'none'
            end_reason = 'buffer overflow counter'
            
        elif end_word.startswith(preamble['wEPM']):
            epoch_counter = int(end_word[4:16], 2)
            num_data = epoch_counter
            hit_type = 'none'
            end_reason = 'epoch counter'

        eoms.append((end_reason, hit_type, num_data))
    return eoms


#-------------------------------------------------------------------------------
# get info from info words
#-------------------------------------------------------------------------------
def getInfo(message):
    info_words = [word for (i, word) in message
                  if word.startswith(preamble['wINF'])]
    return [(infotype_str[word[4:8]], int(word[8:12],2)) for word in info_words]
    #        info                     channelID



        
#-------------------------------------------------------------------------------
# MAIN
#-------------------------------------------------------------------------------
recordedData = []

verbose = False
if len(sys.argv) > 1:
    verbose = (sys.argv[1] == '-v')

#-------------------------------------------------------------------------------
# get all messages and infos
#-------------------------------------------------------------------------------
switchOutputData = readSimOutputFile('switchOutputData_raw.txt')
messages = list(splitSwitchOutputData(switchOutputData))

num_messages = len(messages)
size_messages = sum(len(message) for message in messages) * 2 # bytes

print 'found %i messages' % num_messages
print '    total size: %i bytes' % size_messages
print '    average: %.2f bytes' % (float(size_messages)/num_messages)

#-------------------------------------------------------------------------------
# analyze each message
#-------------------------------------------------------------------------------
for (i, message) in enumerate(messages):
    print '\n----------------------------------------------------------------------'
    print '%4i of %i' % (i+1, num_messages)
    print '----------------------------------------------------------------------'

    if verbose:
        print '\n'.join('%5i: %s' % (i, word) for (i, word) in message) + '\n'

    for (group, channel) in getGroupIdChannelId(message):
        print 'group: %i\nchannel: %i' % (group, channel)

    timestamps = getTimestamps(message)
    if len(timestamps) > 0:
        print 'timestamp(s):', ' '.join(str(timestamp)
                                        for timestamp in timestamps)

    data_parts = getRawData(message)
    if len(data_parts):
        print 'data:', '\n      '.join(str(data) for data in data_parts)

    for (end_reason, hit_type, num_data) in getEndOfMessage(message):
        print 'end of message:'
        print '    reason: %s' % end_reason
        print '    hit type: %s' % hit_type
        print '    number of data values: %i' % num_data

    for (info, channel) in getInfo(message):
        print 'info:', info
        print 'channel:', channel



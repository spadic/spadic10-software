#!/usr/bin/python

from spadic_message_lib import *
from spadic_control_lib import *


if __name__=='__main__':
    # open FTDI -> IO Manager -> Test Data Out connection
    s = SpadicTestDataOut()
    # read some bytes
    b = s.read_data(1000)
    # convert bytes to 16 bit words
    w = message_words(b)
    # split words into messages
    m = messages(w)
    # create Message objects from raw data
    M = [Message(mi) for mi in m]

    # how many did we get?
    print 'got %i messages.' % len(M)
    # are there any info messages?
    print 'got %i info messages.' % len([Mi for Mi in M
                                         if Mi.info_type is not None])
    # are there any buffer overflow messages?
    print 'got %i buffer overflow messages.' % len([Mi for Mi in M
                             if Mi.buffer_overflow_count is not None])

    # show some messages
    print M[0]
    print M[1]
    print M[2]

    # print data in gnuplot format
    print M[0].data_gnuplot()
    # what if the data selection mask is 111110011010101?
    print M[0].data_gnuplot('111110011010101')


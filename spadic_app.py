import time
import random
import spadic

# setup
#====================================================================

s = spadic.Spadic()
c = spadic.Controller(s)
r = spadic.MessageReader(s)

# for interactive use
c.set_directmode(True)


# configs
#====================================================================

def config_ftdireadtest():
    mode = c._directmode
    c.set_directmode(False) # avoid numerous write operations
    c.reset()

    c.testdata(testdatain=True, testdataout=True)
    c.digital.channel[0](enable=True)

    c.apply()
    c.set_directmode(mode)

#--------------------------------------------------------------------

def config_analogtest(channel):
    mode = c._directmode
    c.set_directmode(False) # avoid numerous write operations
    c.reset()

    
    # global analog settings
    c.frontend(frontend='P', baseline=64,
               psourcebias=60, nsourcebias=60,
               pcasc=60, ncasc=60, xfb=60)
    c.adcbias(vndel=70, vpdel=100, vploadfb=70,
              vploadfb2=70, vpfb=70, vpamp=70)

    # global digital settings
    c.filter.stage[4](scaling=0.5, norm=True, offset=128, enable=1)
    c.comparator(threshold1=20, threshold2=30, diffmode=0)
    c.hitlogic(mask=0xFFFFF000, window=20)
    c.testdata(testdatain=1, testdataout=1,
               group={0: 'A', 1: 'B'}[channel//16])

    # channel settings
    c.digital.channel[channel](enable=1)
    c.frontend.channel[channel](baseline=64, enablecsa=1, enableadc=1)

    c.apply()
    c.set_directmode(mode)

#--------------------------------------------------------------------

def config_adctest(channel):
    mode = c._directmode
    c.set_directmode(False) # avoid numerous write operations
    c.reset()
    
    # global analog settings
    c.frontend(frontend='P', baseline=64,
               psourcebias=60, nsourcebias=60,
               pcasc=60, ncasc=60, xfb=60)
    c.adcbias(vndel=70, vpdel=100, vploadfb=70,
              vploadfb2=70, vpfb=70, vpamp=70)

    # global digital settings
    c.hitlogic(mask=0xFFFF0000, window=16)
    c.testdata(testdatain=1, testdataout=1, group='A')

    # setup channel 0 --> channel x trigger
    c.digital.channel[0](enable=True)
    c.digital.channel[channel](enable=True)
    c.digital.neighbor['A'](source=0, target=channel, enable=1)
    c.frontend.channel[channel](baseline=64, enablecsa=1, enableadc=1)

    c.apply()
    c.set_directmode(mode)


# utility
#====================================================================

def ledtest():
    """Turn one LED on and off."""
    mode = c._directmode
    c.set_directmode(True)
    c.led(1, 0)
    c.led(0, 0)
    c.set_directmode(mode)

#--------------------------------------------------------------------

def randdata(n):
    """Generate a list of random numbers."""
    return [random.randint(0, 120) for i in range(n)]

#--------------------------------------------------------------------
    
def ftdireadtest(f=None, max_timeout=1, timeout_init=1e-6):
    """Read from FTDI until empty, and print as hexadecimal codes."""
    start = time.time()
    timeout = timeout_init
    print >> f, ''
    while True:
        d = s._ftdi_read(9, 1)
        if d:
            timeout = timeout_init
            print >> f, '%6.1f: ' % (time.time()-start) + \
                        ' '.join('%02X' % x for x in d)
        else:
            if timeout > max_timeout:
                break
            time.sleep(timeout)
            timeout = 2*timeout

#--------------------------------------------------------------------

def quickwrite(data):
    """Write data to channel 0 and read back from received messages."""
    for i in range(4):
        s.write_data(data)
        time.sleep(0.1)
    M = r.read()
    if M:
        return M[-1].data
    else:
        print 'no messages found!'


import time
import random
import spadic

#from spadic.basic import SpadicDummy
#s = SpadicDummy()
s = spadic.Spadic()
c = spadic.Controller(s)
r = spadic.MessageReader(s)

# for interactive use
c.set_directmode(True)


def ledtest():
    mode = c._directmode
    c.set_directmode(True)
    c.led(1, 0)
    c.led(0, 0)
    c.set_directmode(mode)


def config_ftdireadtest():
    mode = c._directmode
    c.set_directmode(False) # avoid numerous write operations
    c.reset()

    c.testdata(testdatain=True, testdataout=True)
    c.digital.channel[0](enable=True)

    c.apply()
    c.set_directmode(mode)


def config_analogtest():
    mode = c._directmode
    c.set_directmode(False) # avoid numerous write operations
    c.reset()

    # global analog settings
    c.frontend(frontend='P', baseline=10,
               psourcebias=60, nsourcebias=60,
               pcasc=60, ncasc=60, xfb=60)
    c.adcbias(vndel=70, vpdel=100, vploadfb=70,
              vploadfb2=70, vpfb=70, vpamp=70)

    # global digital settings
    c.filter.stage[4](scaling=0.5, norm=True, offset=128, enable=1)
    c.comparator(threshold1=20, threshold2=30, diffmode=0)
    c.hitlogic(mask=0xFFFFF000, window=20)
    c.testdata(testdatain=1, testdataout=1, group='A')

    # channel settings
    c.digital.channel[0](enable=1)
    c.frontend.channel[0](baseline=10, enablecsa=1, enableadc=1)

    c.apply()
    c.set_directmode(mode)


def config_adctest():
    mode = c._directmode
    c.set_directmode(False) # avoid numerous write operations
    c.reset()
    
    # global analog settings
    c.frontend(frontend='P', baseline=10,
               psourcebias=60, nsourcebias=60,
               pcasc=60, ncasc=60, xfb=60)
    c.adcbias(vndel=70, vpdel=100, vploadfb=70,
              vploadfb2=70, vpfb=70, vpamp=70)

    # global digital settings
    c.hitlogic(mask=0xFFFFF000, window=20)
    c.testdata(testdatain=1, testdataout=1, group='A')

    # setup channel 0 --> channel 3 trigger
    c.digital.channel[0](enable=True)
    c.digital.channel[3](enable=True)
    c.digital.neighbor['A'](source=0, target=3, enable=1)
    c.frontend.channel[3](baseline=10, enablecsa=1, enableadc=1)

    c.apply()
    c.set_directmode(mode)



def randdata(n):
    return [random.randint(0, 120) for i in range(n)]

    
def ftdireadtest(f=None, max_timeout=1, timeout_init=1e-6):
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


def quickwrite(data):
    for i in range(4):
        s.write_data(data)
        time.sleep(0.1)
    M = r.read()
    if M:
        return M[-1].data
    else:
        print 'no messages found!'


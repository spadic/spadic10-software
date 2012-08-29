import time
import random
import spadic

#from spadic.basic import SpadicDummy
#s = SpadicDummy()
s = spadic.Spadic()
c = spadic.Controller(s)
r = spadic.MessageReader(s)


def ledtest():
    c.led(1, 0)
    c.led(0, 0)


def config_ftdireadtest():
    c.reset()
    c.testdata(testdatain=True, testdataout=True)
    c.digital.channel[0](enable=True)
    c.apply()


def config_analogtest():
    c.reset()
    # analog settings
    c.frontend(frontend='P', baseline=10,
               psourcebias=60, nsourcebias=60,
               pcasc=60, ncasc=60, xfb=60)
    c.frontend.channel[31](baseline=10, enablecsa=1, enableadc=1)
    c.adcbias(vndel=70, vpdel=100, vploadfb=70,
              vploadfb2=70, vpfb=70, vpamp=70)

    # digital settings
    c.comparator(threshold1=-255, threshold2=-210, diffmode=0)
    c.hitlogic(mask=0xFFFFF000, window=20)
    c.digital.channel[31](enable=1)
    c.testdata(testdatain=1, testdataout=1, group='B')
    c.apply()


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


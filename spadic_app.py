import time
import random
import spadic

s = spadic.Spadic()
c = spadic.Controller(s)
r = spadic.MessageReader(s)

def ledtest():
    c.leds(1, 0)
    c.leds(0, 0)

# TODO: include in Controller
def enablechannel0(x):
    if x not in [0, 1]:
        raise ValueError('only 0 or 1 allowed!')
    c.registerfile['REG_disableChannelA'] = 0xFFFF-x
    c.registerfile['REG_disableChannelB'] = 0xFFFF

def config_ftdireadtest():
    c.clear_shiftregister()
    c.testdata(inp=True, out=True)
    enablechannel0(1)
    c.hitlogic(mask=0xFFFF0000, window=16)
    c.comparator(0, 0, 0) # diffmode off

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


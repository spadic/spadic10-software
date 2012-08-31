#!/usr/bin/env python

dec = [['VCascNFB', 'VNFB', 'VNDel'],
       ['VCascNFB', 'VNFB', 'VNDel'],
       ['RefFB', 'RefNwell', 'AmpCasc'],
       ['RefFB', 'RefNwell', 'AmpCasc'],
       ['VPLoadFB', 'VPAmp', 'VPDel'],
       ['VPAmp', 'VCascPFB', 'VPFB'],
       ['VPFB', 'VPLoadFB2', 'analogTrigger']]

import itertools
allcomb = list(itertools.product(*dec))
comb = set(frozenset(c) for c in allcomb if len(set(c))==7)
comb_left = [list(c) for c in comb]


v_all = [v for d in dec for v in d]
v_in = []

while len(v_in) < 7:
    print ('current voltage selection (%i/7): '
           '[' + ', '.join(v_in) + ']') % len(v_in)

    print len(comb_left), 'possible combinations left'

    v_left = dict((i, v) for (i, v) in enumerate(sorted(
                  set(v for c in comb_left for v in c
                      if v not in v_in))))

    print len(v_left), 'voltages left:'
    print '\n'.join('%2i: %s' % (i, v) for (i, v) in v_left.iteritems())

    i = raw_input('choose the voltage you want to include: ')
    v_chosen = v_left[int(i)]

    v_in.append(v_chosen)
    comb_left = [c for c in comb_left if v_chosen in c]

    print ''

print 'final voltage selection: [' + ', '.join(v_in) + ']'
comb_final = [c for c in allcomb if all(v in c for v in v_in)]
print len(comb_final), 'combinations for this selection:'
for (i, c) in enumerate(comb_final):
    print 'combination %i:' % i
    print 'pad enable voltage'
    for ip in range(7):
        en = [en for en in range(3) if dec[ip][en]==c[ip]][0]
        print ' %i   %i     %s' % (ip+1, en+1, c[ip])


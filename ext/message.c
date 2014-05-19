#include <stdlib.h>

#include "message.h"
#include "message_helper.h"

#include <stdio.h>

//===================================================================
// private functions
//===================================================================

int has_preamble(unsigned short w, struct Preamble p)
{
    return (w & p.mask) == p.value;
}

//-------------------------------------------------------------------

void message_init(Message* m)
{
    if (m == NULL)
        return;
    m->valid = 0;
    m->data = NULL;
}

//===================================================================
// public functions
//===================================================================

Message* message_new(void)
{
    Message* m;
    m = malloc(sizeof *m);
    message_init(m);
    return m;
}

//-------------------------------------------------------------------

void message_delete(Message* m)
{
    free(m->data);
    free(m);
}

//-------------------------------------------------------------------

unsigned short* read_message(unsigned short* begin, unsigned short* end,
                             Message* m)
{
    Message _m;
    unsigned short* w;
    for (w=begin; w<end; w++) {
        printf("word: %04X\n", *w);

        // start of message -> group ID, channel ID
        if (has_preamble(*w, wSOM)) {
            _m.group_id = (*w & 0x0FF0) >> 4;
            _m.channel_id = (*w & 0x000F);
            _m.valid |= 0x01;

        // timestamp
        } else if (has_preamble(*w, wTSW)) {
            _m.timestamp = (*w & 0x0FFF);
            _m.valid |= 0x02;

        // data...

        // end of message -> num. data, hit type, stop type
        } else if (has_preamble(*w, wEOM)) {
            _m.num_data = (*w & 0x0FC0) >> 6;
            _m.hit_type = (*w & 0x0030) >> 4;
            _m.stop_type = (*w & 0x0007);
            _m.valid |= 0x08;

        // buffer overflow count
        } else if (has_preamble(*w, wBOM)) {
            _m.buffer_overflow_count = (*w & 0x00FF);
            _m.valid |= 0x10;

        // epoch marker
        } else if (has_preamble(*w, wEPM)) {
            _m.epoch_count = (*w & 0x0FFF);
            _m.valid |= 0x20;

        // info words
        } else if (has_preamble(*w, wINF)) {
            _m.info_type = (*w & 0x0F00) >> 8;
            if any(has_preamble(*w, t])
                   for it in ['iDIS', 'iNGT', 'iNBE', 'iMSB']):
                _m.channel_id = (w & 0x00F0) >> 4
            } else if ( has_preamble(*w, iSYN)) {
                _m.epoch_count = (w & 0x00FF)
        }
    }
    return w+1;
}

static int infotype_has_channel_id(unsigned char info_type)
{
    switch (info_type) {
        case 0: return 1; // iDIS
        case 1: return 1; // iNGT
        case 3: return 1; // iNBE
        case 4: return 1; // iMSB
    }
    return 0; // TODO use enum
}

//===================================================================
// test/temp/dummy/wrap
//===================================================================

int seek_message_start_all(unsigned short* begin, unsigned short* end)
{
    Message m;
    int count = 0;
    unsigned short* pw = begin;
    while (pw<end) {
        printf("pw: %u\n", pw);
        pw = read_message(pw, end, &m);
        count++;
    }
    return count;
}

//-------------------------------------------------------------------

int seek_message_start_all_wrap(unsigned short* begin, unsigned int length)
{
    return seek_message_start_all(begin, begin+length);
}

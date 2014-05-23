#include <stdlib.h>
#include "message.h"

/* move here again when cleaned up */
#include "message_helper.h"

/*==== private functions ==========================================*/

void ptr_set_null(void *p)
{
    if (p != NULL) {
        free(p);
        p = NULL;
    }
}

void message_init(Message *m)
{
    if (!m) return;
    ptr_set_null(m->samples);
    ptr_set_null(m->raw_buf);
    m->raw_count = 0;
    m->valid = 0;
}

void message_fill(Message *m, uint16_t w)
{
    if (!m) return;
    const Wordtype *t = word_get_type(w);
    if (t != NULL) {
        (t->fill)(m, w);
        m->valid |= t->valid;
    }
}

/*-----------------------------------------------------------------*/

int word_is_type(uint16_t w, const Wordtype *t)
{
    return (w & t->mask) == t->value;
}

const Wordtype *word_get_type(uint16_t w)
{
    static const Wordtype *t[9] = {&wSOM, &wTSW, &wRDA, &wEOM, &wBOM,
                                   &wEPM, &wEXD, &wINF, &wCON};
    int i;
    for (i=0; i<9; i++) {
        if (word_is_type(w, t[i])) { return t[i]; };
    }
    return NULL;
}

int word_is_ignore(uint16_t w)
{
    if (!word_is_type(w, &wINF)) { return 0; }
    else { return word_get_info_type(w) == iNOP; }
}

int word_is_start(uint16_t w)
{
    if (word_is_type(w, &wSOM)) {
        return 1;
    } else if (!word_is_type(w, &wINF)) {
        return 0;
    } else {
        return (word_get_info_type(w) == iNGT ||
                word_get_info_type(w) == iNRT ||
                word_get_info_type(w) == iNBE);
    }
}

int word_is_end(uint16_t w)
{
    return (word_is_type(w, &wEOM) ||
            word_is_type(w, &wBOM) ||
            word_is_type(w, &wEPM) ||
            word_is_type(w, &wINF));
}

/*-----------------------------------------------------------------*/

uint8_t word_get_info_type(uint16_t w)
{
    return (w & 0x0F00) >> 8;
}

/* m != NULL must be checked outside of all fill_wXXX functions */

static void fill_wSOM(Message *m, uint16_t w)
{
    m->group_id = (w & 0x0FF0) >> 4;
    m->channel_id = (w & 0x000F);
}

static void fill_wTSW(Message *m, uint16_t w)
{
    m->timestamp = (w & 0xFFF);
}

static void fill_wRDA(Message *m, uint16_t w)
{
    /* TODO append word to temporary buffer */
}

static void fill_wEOM(Message *m, uint16_t w)
{
    m->num_samples = (w & 0x0FC0) >> 6;
    m->hit_type = (w & 0x0030) >> 4;
    m->stop_type = (w & 0x0007);
}

static void fill_wBOM(Message *m, uint16_t w)
{
    m->buffer_overflow_count = (w & 0x00FF);
}

static void fill_wEPM(Message *m, uint16_t w)
{
    m->epoch_count = (w & 0x0FFF);
}

static void fill_wEXD(Message *m, uint16_t w)
{ /* not implemented in SPADIC 1.0 */
}

static void fill_wINF(Message *m, uint16_t w)
{
    uint8_t t = word_get_info_type(w);
    m->info_type = t;
    if (t == iDIS || t == iNGT || t == iNBE || t == iMSB) {
        m->channel_id = (w & 0x00F0) >> 4;
    } else if (t == iSYN) {
        m->epoch_count = (w & 0x00FF);
    }
}

static void fill_wCON(Message *m, uint16_t w)
{
    /* TODO append word to temporary buffer */
}

/*==== public functions ===========================================*/

Message *message_new(void)
{
    Message *m;
    m = malloc(sizeof *m);
    m->samples = NULL;
    m->raw_buf = NULL;
    message_init(m);
    return m;
}

void message_delete(Message *m)
{
    free(m->samples);
    free(m->raw_buf);
    free(m);
}

/*-----------------------------------------------------------------*/

size_t message_read_from_buffer(Message *m,
                                const uint16_t *buf, size_t len)
{
    uint16_t w;
    size_t n = 0;

    while (n<len) {
        w = buf[n++];
        if (word_is_ignore(w)) { continue; }
        if (word_is_start(w)) { message_init(m); }
        message_fill(m, w);
        if (word_is_end(w)) { break; }
    }
    return n;
}

/*-----------------------------------------------------------------*/

int message_is_hit(Message *m)
{
    return ((m->valid == (wSOM.valid | wTSW.valid |
                          wRDA.valid | wEOM.valid)) ||
            ((m->valid == wINF.valid) &&
             (m->info_type == iDIS || m->info_type == iMSB)));
}

int message_is_buffer_overflow(Message *m)
{
    return (m->valid == (wSOM.valid | wTSW.valid | wBOM.valid));
}

int message_is_epoch_marker(Message *m)
{
    return ((m->valid == (wSOM.valid | wEPM.valid)) ||
            ((m->valid == (wSOM.valid | wINF.valid)) &&
             (m->info_type == iSYN)));
}

int message_is_info(Message *m)
{
    return ((m->valid == wINF.valid) &&
            (m->info_type == iNGT ||
             m->info_type == iNRT ||
             m->info_type == iNBE));
}

int message_is_valid(Message *m)
{
    return (message_is_hit(m) ||
            message_is_buffer_overflow(m) ||
            message_is_epoch_marker(m) ||
            message_is_info(m));
}

int message_is_complete(Message *m)
{
    return ((m->valid & wEOM.valid) ||
            (m->valid & wBOM.valid) ||
            (m->valid & wEPM.valid) ||
            (m->valid & wINF.valid));
}

/*-----------------------------------------------------------------*/

uint8_t message_get_group_id(const Message *m)
{
    /* TODO */
}

uint8_t message_get_channel_id(const Message *m)
{
    /* TODO */
}

uint16_t message_get_timestamp(const Message *m)
{
    /* TODO */
}

int16_t *message_get_samples(const Message *m)
{
    /* TODO */
}

uint8_t message_get_num_samples(const Message *m)
{
    /* TODO */
}

uint8_t message_get_hit_type(const Message *m)
{
    /* TODO */
}

uint8_t message_get_stop_type(const Message *m)
{
    /* TODO */
}

uint8_t message_get_buffer_overflow_count(const Message *m)
{
    /* TODO */
}

uint16_t message_get_epoch_count(const Message *m)
{
    /* TODO */
}

uint8_t message_get_info_type(const Message *m)
{
    /* TODO */
}


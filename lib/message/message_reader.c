/** \author Michael Krieger */

#include <stdlib.h>
#include "message_reader.h"

static void reader_init(MessageReader *r);
struct buf_item;
struct buf_queue;
static void buf_queue_init(struct buf_queue *q);
static void buf_queue_append(struct buf_queue *q, struct buf_item *b);
static struct buf_item *buf_queue_pop(struct buf_queue *q);
static int buf_queue_is_empty(struct buf_queue *q);

struct buf_item {
    const uint16_t *buf;
    size_t len;
    struct buf_item *next;
};

struct buf_queue {
    struct buf_item *begin;
    struct buf_item *end;
};

void buf_queue_init(struct buf_queue *q)
{
    q->begin = NULL;
    q->end = NULL;
}

void buf_queue_append(struct buf_queue *q, struct buf_item *b)
{
    b->next = NULL;
    struct buf_item *end = q->end;
    if (end) {
        end->next = b;
    } else {
        q->begin = b;
    }
    q->end = b;
}

struct buf_item *buf_queue_pop(struct buf_queue *q)
{
    struct buf_item *b = q->begin;
    if (b) {
        q->begin = b->next;
        if (!b->next) {
            q->end = NULL;
        }
    }
    return b;
}

int buf_queue_is_empty(struct buf_queue *q)
{
    return !q->begin;
}

struct message_reader {
};

MessageReader *message_reader_new(void)
{
    MessageReader *r;
    if (r = malloc(sizeof *r)) {
        reader_init(r);
    }
    return r;
}

void reader_init(MessageReader *r)
{
}

void message_reader_delete(MessageReader *r)
{
}

void message_reader_reset(MessageReader *r)
{
}

int message_reader_add_buffer(MessageReader *r, const uint16_t *buf, size_t len)
{
}

Message *message_reader_get_message(MessageReader *r)
{
}

int message_reader_is_empty(MessageReader *r)
{
}

const uint16_t *message_reader_get_depleted(MessageReader *r)
{
}


#if 0

Message *message_reader_next_message(MessageReader *r)
{
    uint16_t *buf = r->buf_current;
    size_t len = r->len_current;
    Message *m = r->message_current;

read:
    size_t n = message_read_from_buffer(m, buf, len);
    if (n < len) {
        buf += n;
        len -= n;
        goto save_new;
    }

next_buf:
    if (message_reader_next_buffer(r)) { /* ? */
        buf = r->buf_current;
        len = r->len_current;
    } else {
        

    if (message_is_complete(m)) {
        goto save_new;
    } else {
        goto read;
    }

save_new:
    r->buf_current = buf;
    r->len_current = len;
    r.message_current = message_new(); /* what if NULL */
    return m;
}

/*---- no goto -----------------------------------------------------*/

struct work_item {
    Message *m;
    const uint16_t *buf;
    size_t len;
};

Message *message_reader_get_message(MessageReader *r)
{
    /* load state */
    struct work_item *w = r->current_work;
    if (!w) { return NULL; }
    const uint16_t *buf = w->buf;
    size_t len = w->len;
    Message *m = w->m;
    if (!buf || !len || !m) { return NULL; } /* or make sure this cannot happen */

    size_t n = message_read_from_buffer(m, buf, len);
    if (n < len) {
        buf += n;
        len -= n;
    }
}

#endif

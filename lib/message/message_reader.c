/** \author Michael Krieger */

#include <stdlib.h>
#include "message_reader.h"

/*==== private declarations ========================================*/

struct buf_item;
struct buf_queue;
static void buf_queue_init(struct buf_queue *q);
static void buf_queue_append(struct buf_queue *q, struct buf_item *b);
static struct buf_item *buf_queue_pop(struct buf_queue *q);
static int buf_queue_is_empty(struct buf_queue *q);

struct reader_state;
static void reader_init(MessageReader *r);
static void reader_clear_buf_queue(struct buf_queue *q);

/*==== implementation ==============================================*/

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

/*------------------------------------------------------------------*/

struct reader_state {
    size_t pos;
    Message *message;
};

struct message_reader {
    struct buf_queue buffers;
    struct buf_queue depleted;
    struct reader_state state;
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
    buf_queue_init(&r->buffers);
    buf_queue_init(&r->depleted);
    message_reader_reset(r);
}

void message_reader_delete(MessageReader *r)
{
    reader_clear_buf_queue(&r->buffers);
    reader_clear_buf_queue(&r->depleted);
    free(r);
}

void message_reader_reset(MessageReader *r)
{
    struct buf_item *b;
    while (b = buf_queue_pop(&r->buffers)) {
        buf_queue_append(&r->depleted, b);
    }
    r->state = (struct reader_state){.pos=0, .message=NULL};
}

int message_reader_add_buffer(MessageReader *r, const uint16_t *buf, size_t len)
{
    if (!buf || !len) { return 1; }
    struct buf_item *b;
    if (!(b = malloc(sizeof *b))) { return 1; }
    b->buf = buf;
    b->len = len;
    buf_queue_append(&r->buffers, b);
    return 0;
}

void reader_clear_buf_queue(struct buf_queue *q)
{
    struct buf_item *b;
    while (b = buf_queue_pop(q)) {
        free(b);
    }
}

Message *message_reader_get_message(MessageReader *r)
{
    /* load state */
    struct reader_state s = r->state;
    Message *m = s.message;
    if (!m && !(m = message_new())) { return NULL; }
    size_t pos = s.pos;

    /* read */
    struct buf_item *b;
    const uint16_t *buf;
    size_t len;
    while (1) {
        if (!(b = r->buffers.begin)) {
            s.message = m;
            m = NULL;
            break;
        }
        buf = b->buf;
        len = b->len;

        pos += message_read_from_buffer(m, buf+pos, len-pos);
        if (pos < len) {
            s.message = NULL;
            break;
        } else {
            buf_queue_append(&r->depleted, buf_queue_pop(&r->buffers));
            pos = 0;
            if (message_is_complete(m)) {
                s.message = NULL;
                break;
            }
        }
    }

    /* save state */
    s.pos = pos;
    r->state = s;
    return m;
}

int message_reader_is_empty(MessageReader *r)
{
    return buf_queue_is_empty(&r->buffers);
}

const uint16_t *message_reader_get_depleted(MessageReader *r)
{
    struct buf_item *b = buf_queue_pop(&r->depleted);
    if (!b) { return NULL; }
    const uint16_t *buf = b->buf;
    free(b);
    return buf;
}

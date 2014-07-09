/** \author Michael Krieger */

#include <stdlib.h>
#include "message.h"
#include "message_reader.h"

/*==== private declarations ========================================*/

struct msg_item;
struct msg_queue;
static void msg_queue_init(struct msg_queue *q);
static void msg_queue_clear(struct msg_queue *q);
static void msg_queue_append(struct msg_queue *q, struct msg_item *t);
static struct msg_item *msg_queue_pop(struct msg_queue *q);
static int msg_queue_is_empty(struct msg_queue *q);

struct reader_state;
static void reader_state_init(struct reader_state *s);
static void reader_init(MessageReader *r);

/*==== implementation ==============================================*/

struct msg_item {
    Message *msg;
    struct msg_item *next;
};

struct msg_queue {
    struct msg_item *begin;
    struct msg_item *end;
};

void msg_queue_init(struct msg_queue *q)
{
    q->begin = NULL;
    q->end = NULL;
}

void msg_queue_clear(struct msg_queue *q)
{
    struct msg_item *t;
    while (t = msg_queue_pop(q)) {
        message_delete(t->msg);
        free(t);
    }
}

void msg_queue_append(struct msg_queue *q, struct msg_item *t)
{
    t->next = NULL;
    struct msg_item *end = q->end;
    if (end) {
        end->next = t;
    } else {
        q->begin = t;
    }
    q->end = t;
}

struct msg_item *msg_queue_pop(struct msg_queue *q)
{
    struct msg_item *t = q->begin;
    if (t) {
        q->begin = t->next;
        if (!t->next) {
            q->end = NULL;
        }
    }
    return t;
}

int msg_queue_is_empty(struct msg_queue *q)
{
    return !q->begin;
}

/*------------------------------------------------------------------*/

struct reader_state {
    size_t pos;
    Message *message;
};

void reader_state_init(struct reader_state *s)
{
    s->pos = 0;
    s->message = NULL;
}

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
    reader_state_init(&r->state);
}

void message_reader_delete(MessageReader *r)
{
    reader_clear_buf_queue(&r->buffers);
    reader_clear_buf_queue(&r->depleted);
    if (r->state.message) {
        message_delete(r->state.message);
    }
    free(r);
}

void message_reader_reset(MessageReader *r)
{
    struct buf_item *b;
    while (b = buf_queue_pop(&r->buffers)) {
        buf_queue_append(&r->depleted, b);
    }
    if (r->state.message) {
        message_delete(r->state.message);
    }
    reader_state_init(&r->state);
}

int message_reader_add_buffer(MessageReader *r, const uint16_t *buf, size_t len)
{
    struct buf_item *b;
    if (!(b = malloc(sizeof *b))) { return 1; }
    b->buf = buf;
    b->len = len;
    buf_queue_append(&r->buffers, b);
    return 0;
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

const uint16_t *message_reader_get_depleted(MessageReader *r)
{
    struct buf_item *b = buf_queue_pop(&r->depleted);
    if (!b) { return NULL; }
    const uint16_t *buf = b->buf;
    free(b);
    return buf;
}

int message_reader_is_empty(MessageReader *r)
{
    return buf_queue_is_empty(&r->buffers);
}

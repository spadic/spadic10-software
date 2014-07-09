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
static void msg_queue_extend(struct msg_queue *q, struct msg_queue *r);
static struct msg_item *msg_queue_pop(struct msg_queue *q);
static int msg_queue_is_empty(struct msg_queue *q);

static int reader_init(MessageReader *r);
static void reader_clear(MessageReader *r);

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

void msg_queue_extend(struct msg_queue *q, struct msg_queue *r)
{
    struct msg_item *end = q->end;
    if (end) {
        end->next = r->begin;
        if (r->end) {
            q->end = r->end;
        }
    } else {
        q = r;
    }
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

struct message_reader {
    struct msg_queue messages;
    Message *msg;
};

MessageReader *message_reader_new(void)
{
    MessageReader *r;
    if (!(r = malloc(sizeof *r))) {
        return NULL;
    }
    if (!(reader_init(r))) {
        message_reader_delete(r);
        return NULL;
    }
    return r;
}

int reader_init(MessageReader *r)
{
    msg_queue_init(&r->messages);
    if (!(r->msg = message_new())) {
        return 1;
    }
    return 0;
}

void message_reader_delete(MessageReader *r)
{
    msg_queue_clear(&r->messages);
    if (r->msg) {
        message_delete(r->msg);
    }
    free(r);
}

void message_reader_reset(MessageReader *r)
{
    msg_queue_clear(&r->messages);
    if (r->msg) {
        message_reset(r->msg);
    }
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

Message *message_reader_get_message(MessageReader *r)
{
    struct msg_item *t = msg_queue_pop(&r->messages);
    if (!t) { return NULL; }
    Message *m = t->msg;
    free(t);
    return m;
}

int message_reader_is_empty(MessageReader *r)
{
    return buf_queue_is_empty(&r->buffers);
}

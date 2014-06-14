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

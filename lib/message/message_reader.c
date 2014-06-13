Message *message_reader_next_message(MessageReader *r)
{
    uint16_t *buf = r->buf;
    size_t len = r->len;
    Message *m = r->message;

read:
    size_t n = message_read_from_buffer(m, buf, len);
    if (n < len) {
        buf += n;
        len -= n;
        goto save_new;
    }

next_buf:
    struct buf_item b = message_reader_next_buffer(r); /* ? */
    buf = b.buf;
    len = b.len;

    if (message_is_complete(m)) {
        goto save_new;
    } else {
        goto read;
    }

save_new:
    r->buf = buf;
    r->len = len;
    r.message = message_new(); /* what if NULL */
    return m;
}

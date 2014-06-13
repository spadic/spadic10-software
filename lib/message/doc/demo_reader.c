#include "message_reader.h"

size_t dummy_get_buffer(const uint16_t **p);
void dummy_release_buffer(const uint16_t *p);

int main(void)
{
    MessageReader *r = message_reader_new();
    if (!r) { return 1; }

    while (1) {
        /* select next buffer somehow */
        const uint16_t *buf;
        size_t len = dummy_get_buffer(&buf);
        if (!buf) { break; }

        /* add buffer to reader */
        message_reader_add_buffer(r, buf, len);

        /* read messages */
        Message *m;
        while (m = message_reader_get_message(r)) {
            message_delete(m); /* or something useful */
        }

        /* two reasons: buffer empty or failed to create message */
        if (!message_reader_is_empty(r)) { break; }
    }

    /* clean up */
    const uint16_t *buf;
    while (buf = message_reader_get_depleted(r)) {
        dummy_release_buffer(buf);
    }

    message_reader_delete(r);
    return 0;
}

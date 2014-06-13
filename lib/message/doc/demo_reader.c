#include "message_reader.h"

size_t get_buffer(const uint16_t **p);
void release_buffer(const uint16_t *p);

int main(void)
{
    MessageReader *reader = message_reader_new();
    if (!reader) { return 1; }

    while (1) {
        /* select next buffer */
        const uint16_t *buf;
        size_t len = get_buffer(&buf);
        if (!buf) { return 1; }

        /* add buffer to reader */
        message_reader_add_buffer(reader, buf, len);

        /* read messages */
        size_t N;
        do {
            N = message_reader_alloc(reader);

            size_t j;
            for (j = 0; j < N; j++) {
                Message *m = message_reader_next(reader);
            }
        } while (m);
        release_buffer(buf);
    }

    message_reader_delete(reader);
    return 0;
}

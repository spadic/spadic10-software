#include <stdio.h>
#include "message.h"


size_t test_message_read(uint16_t *buf, size_t len)
{
    Message *m = message_new();
    if (!m) { return 0; }

    int count = 0;
    uint16_t *pos = buf;
    ptrdiff_t left = len;
    size_t n;

    while (left > 0) {
        n = message_read_from_buffer(m, pos, left);
        pos += n;
        left -= n;
        if (message_is_valid(m)) {
            count ++;
        }
        printf("n: %d  pos: %d  left: %d\n", n, pos-buf, left);
        getchar();
    }

    return count;
}


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
    size_t num_samples;
    int16_t *samples;

    while (left > 0) {
        n = message_read_from_buffer(m, pos, left);
        pos += n;
        left -= n;
        //printf("n: %d  pos: %d  left: %d\n", n, pos-buf, left);
        getchar();
        count++;
        if (message_is_complete(m) && message_is_hit(m)) {
            num_samples = message_get_num_samples(m);
            samples = message_get_samples(m);
            printf("\n%d: ", num_samples);
            if (samples) {
                int i;
                for (i = 0; i < num_samples; i++) {
                    printf("%d ", samples[i]);
                }
                printf("\n");
            }
        }
    }

    message_delete(m);
    return count;
}

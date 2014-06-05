#include <stdio.h>
#include "message.h"

#define N 15
const uint16_t buf[N] = {
    0x8012,
    0x9666,
    0xA008,
    0x0403,
    0x0100,
    0x5030,
    0x0E00,
    0xB1D0,
    0x8034,
    0x9888,
    0xA008,
/*  0x0403, missing -> raw data invalid */
    0x0100,
    0x5030,
    0x0E00,
    0xB1D0
};

void print_hit_message(Message *m)
{
    printf("group ID: %d\n", message_get_group_id(m));
    printf("channel ID: %d\n", message_get_channel_id(m));
    printf("timestamp: %d\n", message_get_timestamp(m));
    printf("num. samples: %d\n", message_get_num_samples(m));
    printf("hit type: %d\n", message_get_hit_type(m));
    printf("stop type: %d\n", message_get_stop_type(m));
    int16_t *s;
    if (s = message_get_samples(m)) {
        printf("samples: ");
        int i = 0;
        while (i < message_get_num_samples(m)) {
            printf("%d ", s[i++]);
        }
        printf("\n");
    } else {
        printf("raw data invalid\n");
    }
}

int main(void)
{
    Message *m = message_new();

    size_t n = 0;

    while (n < N) {
        n += message_read_from_buffer(m, buf+n, N-n);

        if (!message_is_complete(m)) {
            printf("\nincomplete message\n");
            return 1;
        }

        if (message_is_hit(m)) {
            printf("\nmessage is hit\n");
            print_hit_message(m);
        }
    }

    return 0;
}

#include "message.h"
#include "message_reader.h"

const uint16_t buf1[] = {
    0x8986,
    0x9654,
    0xA010,
    0xB075,
};
const uint16_t buf2[] = {
    0x8ABC,
    0x9DEF,
    0xA020,
    0x0600,
    0xB0A3
};

const size_t len1 = 4;
const size_t len2 = 5;

int main(void)
{
    MessageReader *r = message_reader_new();
    if (!r) { return 1; }

    if (message_reader_add_buffer(r, buf1, len1)) { return 1; }
    if (message_reader_add_buffer(r, buf2, len2)) { return 1; }

    Message *m;
    while (1) {
        m = message_reader_get_message(r);
        if (!m) { break; }
        message_delete(m);
    }

    message_reader_delete(r);
    return 0;
}

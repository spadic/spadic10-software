#include "message.h"
#include "message_int.h"

#include <stdio.h>

int has_preamble(uint16_t w, struct Preamble p)
{
    return (w & p.mask) == p.value;
}

uint16_t* seek_message_start(uint16_t* begin, uint16_t* end)
{
    uint16_t* pw;
    for (pw=begin; pw<end; pw++) {
        printf("word %i: %04X\n", pw-begin, *pw);
        if (has_preamble(*pw, wSOM)) {
            printf("HIT\n");
            goto exit;
        }
    }
    printf("NO HIT\n");
    exit:

    return pw+1;
}

size_t seek_message_start_all(uint16_t* begin, uint16_t* end)
{
    size_t count = 0;
    uint16_t* pw = begin;
    while (pw<end) {
        printf("pw: %i\n", pw);
        pw = seek_message_start(pw, end);
        count++;
    }
    return count;
}

size_t seek_message_start_all_wrap(uint16_t* begin, size_t length)
{
    return seek_message_start_all(begin, (uint16_t*)(begin+length));
}

#include <stddef.h>
#include "message.h"

#include <stdio.h>

int match_word(uint16_t w, struct Pattern t)
{
    return (w & t.mask) == t.value;
}

uint16_t* seek_message_start(uint16_t* begin, uint16_t* end)
{
    uint16_t* p;
    for (p=begin; p<end; p++) {
        printf("word %i: %04X\n", p-begin, *p);
        if (match_word(*p, wSOM)) {
            printf("HIT\n");
            goto exit;
        }
    }
    printf("NO hit\n");
    exit:

    return p+1;
}

size_t seek_message_start_all(uint16_t* begin, uint16_t* end)
{
    size_t count = 0;
    uint16_t* p = begin;
    while (p<end) {
        printf("p: %i\n", p);
        p = seek_message_start(p, end);
        count++;
    }
    return count;
}

size_t seek_message_start_all_wrap(uint16_t* begin, size_t length)
{
    return seek_message_start_all(begin, (uint16_t*)(begin+length));
}

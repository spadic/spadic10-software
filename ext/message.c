#include "message.h"
#include "message_int.h"

#include <stdio.h>

int has_preamble(unsigned short w, struct Preamble p)
{
    return (w & p.mask) == p.value;
}

unsigned short* read_message(unsigned short* begin, unsigned short* end)
{
    unsigned short* pw;
    for (pw=begin; pw<end; pw++) {
        if (has_preamble(*pw, wSOM)) {
            break;
        }
    }
    return pw+1;
}

int seek_message_start_all(unsigned short* begin, unsigned short* end)
{
    int count = 0;
    unsigned short* pw = begin;
    while (pw<end) {
        printf("pw: %u\n", (int)pw&0xFF);
        pw = read_message(pw, end);
        count++;
    }
    return count;
}

int seek_message_start_all_wrap(unsigned short* begin, unsigned int length)
{
    return seek_message_start_all(begin, begin+length);
}

#include <stdio.h>
#include "message.h"

int match_word(uint16_t w, struct Pattern p)
{
    return (w & p.mask) == p.value;
}

// test
int main(void)
{
    uint16_t word[10] = {
      0x8343,
      0x8343,
      0x6303,
      0x5303,
      0x8503,
      0x8503,
      0xB543,
      0xA543,
      0x7543,
      0x8543
    };

    int i;
    for (i=0; i<10; i++) {
        int result = match_word(word+i, wSOM);
        if (result)
            printf("success.\n");
        else
            printf("fail.\n");
    }

    return 0;
}

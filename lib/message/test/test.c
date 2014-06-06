#include <stdio.h>
#include "message.h"

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
        int result = match_word(word[i], wSOM);
        if (result)
            printf("success.\n");
        else
            printf("fail.\n");
    }

    uint16_t input;
    int ninput; 
    printf("enter a number: ");
    ninput = scanf("%hi", &input);

    printf("got %i values\n", ninput);
    printf("you entered %04X\n", input);

    return 0;
}

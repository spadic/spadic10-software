#ifndef SPADIC_MESSAGE_H
#define SPADIC_MESSAGE_H
#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stddef.h>

uint16_t* seek_message_start(uint16_t* begin, uint16_t* end);
size_t seek_message_start_all(uint16_t* begin, uint16_t* end);
size_t seek_message_start_all_wrap(uint16_t* begin, size_t length);

#ifdef __cplusplus
}
#endif
#endif

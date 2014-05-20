#ifndef SPADIC_MESSAGE_H
#define SPADIC_MESSAGE_H
#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>
#include <stdint.h>

typedef struct _message Message;

Message* message_new(void);
void message_delete(Message* m);
uint16_t* read_message(uint16_t* begin, uint16_t* end, Message* m);

#ifdef __cplusplus
}
#endif
#endif

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
uint16_t* message_read_from_buffer(Message* m, uint16_t* buf, size_t len);

#ifdef __cplusplus
}
#endif
#endif

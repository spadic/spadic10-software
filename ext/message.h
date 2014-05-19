#ifndef SPADIC_MESSAGE_H
#define SPADIC_MESSAGE_H
#ifdef __cplusplus
extern "C" {
#endif

typedef struct _message Message;

Message* message_new(void);
void message_delete(Message* m);
unsigned short* read_message(unsigned short* begin, unsigned short* end,
                             Message* m);

#ifdef __cplusplus
}
#endif
#endif

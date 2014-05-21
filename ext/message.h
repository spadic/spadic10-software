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
size_t message_read_from_buffer(Message* m,
                                const uint16_t* buf, size_t len);
/*
 * arguments:
 *   m - pointer to Message object to be filled
 *   buf - pointer to array of 16-bit SPADIC words
 *   len - number of words to be read at most (i.e. length of buf)
 *
 * return value n:
 *   a) If a message could be read, buf+n will point to the word after the
 *      end of the message.
 *   b) Otherwise, buf+n will point to the first word after all words that
 *      are definitely not part of a valid message, i.e. either n == len
 *      if no meaningful data was contained in buf, or n < len if an
 *      incomplete message was contained at the end of buf, but the end is
 *      missing.
 *   In both cases, buf+n points to a location that may be used as the
 *   next value for buf in a repeated call of the function.
 *
 *   Whether a message could be read must be checked using the valid flags
 *   of the message object.
 */
 int message_is_complete(Message* m);

#ifdef __cplusplus
}
#endif
#endif

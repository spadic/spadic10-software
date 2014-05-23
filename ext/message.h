#ifndef SPADIC_MESSAGE_H
#define SPADIC_MESSAGE_H
#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>
#include <stdint.h>

typedef struct _message Message;
Message *message_new(void);
void message_delete(Message *m);

size_t message_read_from_buffer(Message *m,
                                const uint16_t *buf, size_t len);
/*
 * Read words from `buf` and fill message `m`, if possible.
 *
 * The function consumes words from the buffer until either an
 * end-of-message word is encountered or the end of the buffer is reached
 * (i.e. `len` words have been read).
 *
 * The number `n` of consumed words is returned, so that `buf+n` is a
 * suitable value to be passed as the `buf` argument for repeated calls of
 * this function.
 *
 * Different possible cases:
 * key:
 *     ( = start of message
 *     ) = end of message
 *     x = any word except end of message
 *     . = any word except start of message or end of message
 *     | = end of buffer reached
 *
 * a:  xxx(....)  normal case
 * b:  xxx(..|    missing end of message
 * c:  ........)  missing start of message
 * d:  ......|    missing start and end of message
 *
 * It is not guaranteed that a complete message was contained in the
 * consumed words (cases b-d), this can be checked afterwards using
 * `message_is_complete(m)`.
 *
 * The passed message object `m` is reset if, and only if, a
 * start-of-message word is encountered. This means
 * - all words before the last start-of-message word are effectively
 *   ignored, and
 * - cases b-d can be handled by passing the same Message object to
 *   successive calls of this function.
 *
 */

/* query message type and completeness */
int message_is_hit(Message *m);
int message_is_buffer_overflow(Message *m);
int message_is_epoch_marker(Message *m);
int message_is_info(Message *m);
int message_is_valid(Message *m);
int message_is_complete(Message *m);

/* access message data */
uint8_t message_get_group_id(Message *m);
uint8_t message_get_channel_id(Message *m);
uint16_t message_get_timestamp(Message *m);
int16_t *message_get_samples(Message *m);
uint8_t message_get_num_samples(Message *m);
uint8_t message_get_hit_type(Message *m);
uint8_t message_get_stop_type(Message *m);
uint8_t message_get_buffer_overflow_count(Message *m);
uint16_t message_get_epoch_count(Message *m);
uint8_t message_get_info_type(Message *m);

#ifdef __cplusplus
}
#endif
#endif

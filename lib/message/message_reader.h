/**
 * \file
 * \author Michael Krieger
 *
 * This is the API for the SPADIC 1.0 Message Library.
 *
 * **DRAFT**
 */

#ifndef SPADIC_MESSAGE_READER_H
#define SPADIC_MESSAGE_READER_H
#ifdef __cplusplus
extern "C" {
#endif

#include "message.h"

typedef struct message_reader MessageReader;
/**<
 * Context for reading SPADIC messages from buffers.
 */
MessageReader message_reader_new(void);
/**<
 * Allocate and initialize a new message reader.
 * \return Pointer to created message reader, `NULL` if unsuccessful.
 */
void message_reader_delete(MessageReader *r);
/**<
 * Clean up and deallocate a message reader.
 *
 * Nothing is done if `r` is NULL.
 */
void message_reader_reset(MessageReader *r);
/**<
 * Reset a message reader to its initial state.
 *
 * TODO which one?
 * Nothing is done if `r` is NULL.
 * `r` must point to a properly allocated and initialized message reader.
 */
void message_reader_set_buffer(MessageReader *r,
                               const uint16_t *buf, size_t len);
/**<
 * Point the message reader to a new buffer with `len` words.
 *
 * Nothing is done if `buf` is NULL.
 *
 * TODO which one?
 * Nothing is done if `r` is NULL.
 * `r` must point to a properly allocated and initialized message reader.
 */
Message *message_reader_next(MessageReader *r);
/**<
 * Read the next message from the current buffer.
 *
 * \return Pointer to a message object, NULL if the buffer is empty.
 *
 * what if no new message object could be created? (message_new() failed)
 *
 * - message will be complete
 * - must check message_is_valid()
 * - incomplete message will be kept
 */

#ifdef __cplusplus
}
#endif
#endif

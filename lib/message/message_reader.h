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
 * - Nothing is done if `r` is NULL.
 * - `r` must point to a properly allocated and initialized message reader.
 */
size_t message_reader_add_buffer(MessageReader *r,
                                 const uint16_t *buf, size_t len);
/**<
 * Point the message reader to a new buffer with `len` words.
 *
 * Nothing is done if `buf` is NULL.
 *
 * TODO which one?
 * - Nothing is done if `r` is NULL.
 * - `r` must point to a properly allocated and initialized message reader.
 *
 * Attempts to allocate new messages that are subsequently filled.
 *
 * \return Number of currently allocated messages. If this is zero, `buf`
 * was not added.
 */
Message *message_reader_next_message(MessageReader *r);
/**<
 * Read the next message.
 *
 * \return Pointer to a message object, NULL if all buffers are depleted,
 * undefined if called more often than indicated by
 * message_reader_add_buffer().
 *
 * what if no new message object could be created? (message_new() failed)
 *
 * - message will be complete
 * - must check message_is_valid()
 * - incomplete message will be kept
 */
const uint16_t *message_reader_next_depleted_buffer(MessageReader *r);
/**<
 * \return Next depleted buffer, NULL if no depleted buffers are left.
 *
 * Nothing is done if `r` is `NULL`.
 */

#ifdef __cplusplus
}
#endif
#endif

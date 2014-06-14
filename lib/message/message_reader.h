/**
 * \file
 * \author Michael Krieger
 *
 * This is the API for the SPADIC 1.0 Message Library.
 *
 * All functions receiving a pointer `r` to a MessageReader object assume
 * that it has been properly allocated and initialized (by
 * message_reader_new()).
 *
 * **DRAFT**
 */

#ifndef SPADIC_MESSAGE_READER_H
#define SPADIC_MESSAGE_READER_H

#include "message.h"

typedef struct message_reader MessageReader;
/**<
 * Context for reading SPADIC messages from buffers.
 */
MessageReader *message_reader_new(void);
/**<
 * Allocate and initialize a new message reader.
 * \return Pointer to created message reader, `NULL` if unsuccessful.
 */
void message_reader_delete(MessageReader *r);
/**<
 * Clean up and deallocate a message reader.
 */
void message_reader_reset(MessageReader *r);
/**<
 * Reset a message reader to its initial state.
 */
void message_reader_add_buffer(MessageReader *r,
                               const uint16_t *buf, size_t len);
/**<
 * Add a new buffer with `len` words to a message reader.
 *
 * Nothing is done if `buf` is NULL or `len` is zero.
 */
Message *message_reader_get_message(MessageReader *r);
/**<
 * Read the next message.
 *
 * \return Pointer to a message object, if available, `NULL` otherwise.
 *
 * Normally, `NULL` is returned because all buffers are depleted. Check
 * this with message_reader_is_empty().
 *
 * The returned messages are always complete (message_is_complete()).
 */
int message_reader_is_empty(MessageReader *r);
/**<
 * \return Non-zero if all buffers are depleted.
 *
 * Add more buffers to read from with message_reader_add_buffer().
 *
 * If message_reader_get_message() returned `NULL` and the reader is not
 * empty (this function returns zero), an internal error has occurred.
 */
const uint16_t *message_reader_get_depleted(MessageReader *r);
/**<
 * \return Next depleted buffer, NULL if no depleted buffers are left.
 */

#endif

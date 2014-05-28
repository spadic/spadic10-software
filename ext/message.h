#ifndef SPADIC_MESSAGE_H
#define SPADIC_MESSAGE_H
#ifdef __cplusplus
extern "C" {
#endif

/**
 * \file
 * SPADIC 1.0 Message Library
 *
 * Provides functions to extract SPADIC messages from captured raw data
 * and to access the message content.
 */

/**
 * \mainpage
 * You want to look at message.h.
 */

#include <stddef.h>
#include <stdint.h>

/** \name Create, fill and destroy message objects */
/**@{*/
typedef struct message Message;
/**<
 * Represents SPADIC messages.
 */
Message *message_new(void);
/**<
 * Create and initialize a new message object.
 * \return Pointer to created message object, `NULL` if unsuccessful.
 */
void message_delete(Message *m);
/**<
 * Destroy a message object.
 * Nothing is done if `m` is `NULL`.
 */
size_t message_read_from_buffer(Message *m, const uint16_t *buf, size_t len);
/**<
 * Read words from `buf` and fill message `m`.
 *
 * The function consumes words from the buffer until either an
 * end-of-message word is encountered or the end of the buffer is reached
 * (i.e. `len` words have been read).
 *
 * The number `n` of consumed words is returned, so that `buf+n` is a
 * suitable value to be passed as the `buf` argument for repeated calls of
 * this function.
 *
 * Four different cases (`a`--`d`) regarding the occurence of words
 * starting or ending a message are possible:
 *
 *     key:
 *         ( = start of message
 *         ) = end of message
 *         x = any word except end of message
 *         . = any word except start of message or end of message
 *         | = end of buffer reached
 *
 *     a:  xxx(....)  normal case
 *     b:  xxx(..|    missing end of message
 *     c:  ........)  missing start of message
 *     d:  ......|    missing start and end of message
 *
 * It is not guaranteed that a complete message was contained in the
 * consumed words (cases b-d), this can be checked afterwards using
 * message_is_complete().
 *
 * The passed message object `m` is reset if, and only if, a
 * start-of-message word is encountered. This means
 * - all words before the last start-of-message word are effectively
 *   ignored, and
 * - cases b-d can be handled by passing the same Message object to
 *   successive calls of this function.
 *
 * Reading multiple messages from a buffer could then look something like
 * this:
 *
 * \code{.c}
 * uint16_t *pos = buf;
 * ptrdiff_t left = len;
 * Message *m = message_new();
 *
 * size_t n;
 * while (left > 0) {
 *     n = message_read_from_buffer(m, pos, left);
 *     pos += n;
 *     left -= n;
 *     if (message_is_complete(m)) {
 *         do_something_with(m);
 *     }
 * }
 * \endcode
 */
/**@}*/

/**
 * All the following functions assume that `m` is a valid (non-`NULL`)
 * pointer to a message object obtained from message_new().
 */

/** \name Query message status and type */
/**@{*/
int message_is_complete(const Message *m);
/**<
 * \return Non-zero if `m` is a complete message.
 *
 * A message is considered "complete" when both the start and the end of
 * the message have been encountered. Use this function to determine
 * whether message_read_from_buffer() can further fill a given message
 * object.
 *
 * Note that this is different from message_is_valid(): a message can be
 * complete and not valid, but a valid message is always complete.
 */
int message_is_hit(const Message *m);
/**<
 * \return Non-zero if `m` is a regular hit message.
 *
 * Indicates that the following data is available:
 * - group ID (message_get_group_id())
 * - channel ID (message_get_channel_id())
 * - timestamp (message_get_timestamp())
 * - number of samples (message_get_num_samples()),
 *   and the samples themselves (message_get_samples())
 * - hit type (message_get_hit_type())
 * - stop type (message_get_stop_type())
 */
int message_is_hit_aborted(const Message *m);
/**<
 * \return Non-zero if `m` is an aborted hit message.
 *
 * The available data fields are encoded in the returned integer
 * (potentially everything in a normal hit message). The abort reason
 * (channel disabled or data corruption in message builder) is available
 * as the info type (message_get_info_type())
 */
int message_is_buffer_overflow(const Message *m);
/**<
 * \return Non-zero if `m` is a buffer overflow message.
 *
 * Indicates that the following data is available:
 * - group ID (message_get_group_id())
 * - channel ID (message_get_channel_id())
 * - timestamp (message_get_timestamp())
 * - number of lost hits (message_get_buffer_overflow_count()),
 */
int message_is_epoch_marker(const Message *m);
/**<
 * \return Non-zero if `m` is an epoch marker.
 *
 * Indicates that the following data is available:
 * - group ID (message_get_group_id())
 * - epoch count (message_get_epoch_count())
 */
int message_is_epoch_out_of_sync(const Message *m);
/**<
 * \return Non-zero if `m` is an "out of sync" epoch marker.
 *
 * Indicates that the following data is available:
 * - group ID (message_get_group_id())
 * - least significant 8 bits of epoch count (message_get_epoch_count())
 */
int message_is_info(const Message *m);
/**<
 * \return Non-zero if `m` is an info message
 *
 * Indicates that the info type (`NGT`, `NRT`, or `NBE`) is available
 * (message_get_info_type()).
 */
int message_is_valid(const Message *m);
/**<
 * \return Non-zero if `m` is a valid message of any type.
 *
 * Valid messages are of one of the following types:
 * - hit message, normal or aborted
 *   (message_is_hit(), message_is_hit_aborted())
 * - buffer overflow message (message_is_buffer_overflow())
 * - epoch marker, normal or "out of sync"
 *   (message_is_epoch_marker(), message_is_epoch_out_of_sync())
 * - info message (message_is_info())
 */
/**@}*/

/** \name Access message data */
/**@{*/
uint8_t message_get_group_id(const Message *m);
/**< \return The group ID, if available, undefined otherwise. */
uint8_t message_get_channel_id(const Message *m);
/**< \return The channel ID, if available, undefined otherwise. */
uint16_t message_get_timestamp(const Message *m);
/**< \return The timestamp, if available, undefined otherwise. */
int16_t *message_get_samples(const Message *m);
/**<
 * \return Pointer to a memory location containing the samples, if
 * available, `NULL` otherwise.
 *
 * Determine the number of available samples using
 * message_get_num_samples(). The memory containing the samples is
 * reclaimed when `m` is destroyed using message_delete().
 */
uint8_t message_get_num_samples(const Message *m);
/**< \return The number of samples, if available, undefined otherwise. */
uint8_t message_get_hit_type(const Message *m);
/**< \return The hit type, if available, undefined otherwise. */
uint8_t message_get_stop_type(const Message *m);
/**< \return The stop type, if available, undefined otherwise. */
uint8_t message_get_buffer_overflow_count(const Message *m);
/**< \return The buffer overflow count, if available, undefined otherwise. */
uint16_t message_get_epoch_count(const Message *m);
/**< \return The epoch count, if available, undefined otherwise. */
uint8_t message_get_info_type(const Message *m);
/**< \return The info type, if available, undefined otherwise. */
/**@}*/

#ifdef __cplusplus
}
#endif
#endif

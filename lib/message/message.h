/**
 * \file
 * \author Michael Krieger
 *
 * This is the API for the SPADIC 1.0 Message Library.
 */

#ifndef SPADIC_MESSAGE_H
#define SPADIC_MESSAGE_H
#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>
#include <stdint.h>

/**
 * Stop types as returned by message_get_stop_type().
 */
enum stop_types {
    sEND = 0x0, /**< Normal end of message */
    sEBF = 0x1, /**< Channel buffer full */
    sEFF = 0x2, /**< Ordering FIFO full */
    sEDH = 0x3, /**< Multi hit */
    sEDB = 0x4, /**< Multi hit and channel buffer full */
    sEDO = 0x5, /**< Multi hit and ordering FIFO full */
/* unused
    sXX1 = 0x6,
    sXX2 = 0x7,
*/
};

/**
 * Info types as returned by message_get_info_type().
 */
enum info_types {
    iDIS = 0x0, /**< Channel disabled during message building */
    iNGT = 0x1, /**< Next grant timeout */
    iNRT = 0x2, /**< Next request timeout */
    iNBE = 0x3, /**< New grant but channel empty */
    iMSB = 0x4, /**< Corruption in message builder */
    iNOP = 0x5, /**< Empty word */
    iSYN = 0x6, /**< Epoch out of sync */
/* unused
    iXX3 = 0x7,
    iXX4 = 0x8,
    iXX5 = 0x9,
    iXX6 = 0xA,
    iXX7 = 0xB,
    iXX8 = 0xC,
    iXX9 = 0xD,
    iXXA = 0xE,
    iXXB = 0xF,
*/
};

/**
 * Hit types as returned by message_get_hit_type().
 */
enum hit_types {
    hGLB = 0x0, /**< Global trigger */
    hSLF = 0x1, /**< Self triggered */
    hNBR = 0x2, /**< Neighbor triggered */
    hSAN = 0x3, /**< Self and neighbor triggered */
};
typedef struct message Message;
/**<
 * Data structure representing SPADIC 1.0 messages.
 */

/**@{
 * \name Create, fill and destroy message objects
 */
Message *message_new(void);
/**<
 * Allocate and initialize a new message object.
 * \return Pointer to created message object, `NULL` if unsuccessful.
 */
size_t message_size(void);
/**<
 * \return The allocation size for one message object.
 * \note You only need this if you want to allocate memory for message
 * objects yourself. If you use message_new(), you don't need this.
 */
void message_init(Message *m);
/**<
 * Initialize a newly allocated message object.
 *
 * Nothing is done if `m` is `NULL`.
 * This function must be used exactly once for each message object.
 *
 * \note You only need this if you want to allocate memory for message
 * objects yourself. If you use message_new(), you don't need this.
 */
void message_reset(Message *m);
/**<
 * Reset a message object to its initial state.
 *
 * `m` must point to a properly allocated and initialized message object.
 * If this is the case, this function can safely be used any number of
 * times (in contrast to message_init()).
 *
 * Typical use case is to recycle a single message object across multiple
 * calls to message_read_from_buffer() as an alternative to allocating a
 * new message object each time (if the older messages are not needed any
 * longer).
 */
void message_delete(Message *m);
/**<
 * Clean up and deallocate a message object.
 *
 * Nothing is done if `m` is `NULL`.
 *
 * \note You must also use this if you have allocated the message object
 * yourself.
 */
size_t message_read_from_buffer(Message *m, const uint16_t *buf, size_t len);
/**<
 * Read up to `len` words from `buf` and fill message `m`.
 *
 * Nothing is done if `m` is `NULL`.
 *
 * \return The number `n` of consumed words.
 *
 * Words from the buffer are consumed until either
 * - an end-of-message word is encountered (`n` &le; `len`), or
 * - the end of the buffer is reached (`n` = `len`).
 *
 * If `n` = `len`, the two cases can be distinguished by using
 * message_is_complete().
 *
 * The contents of the consumed words are copied into the message object
 * pointed to by `m`. If (and only if) a start-of-message word is
 * encountered, the message object will be reset. This means
 * - all words before the last start-of-message word are effectively
 *   ignored, and
 * - a partially filled message can be reused and possibly completed by
 *   reading from another buffer containing the remaining words.
 */
/**@}*/

/**@{
 * \name Query message status and type
 * All functions in this section assume that `m` points to a
 * properly allocated and initialized message object (e.g. obtained from
 * message_new()).
 */
int message_is_complete(const Message *m);
/**<
 * \return Non-zero if `m` is a complete message.
 *
 * A message is considered "complete" if an end-of-message word has been
 * encountered.
 *
 * Use this function to determine whether a given message object can be
 * further filled by repeated calls of message_read_from_buffer() when
 * `n` = `len` has been returned. If message_read_from_buffer() returns
 * `n` < `len`, the message is complete by definition.
 *
 * Note that this is different from message_is_valid(): a message can be
 * complete and not valid, but a valid message is always complete.
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
 *
 * A "valid" message is always "complete" (message_is_complete()).  If a
 * message is complete, but not valid, there are either words missing that
 * are required for a particular message type or there are additional
 * words making the message type ambiguous.
 */
int message_is_hit(const Message *m);
/**<
 * \return Non-zero if `m` is a regular hit message.
 *
 * Indicates that the following data is available:
 * - group ID (message_get_group_id())
 * - channel ID (message_get_channel_id())
 * - timestamp (message_get_timestamp())
 * - number of samples (message_get_num_samples())
 * - hit type (message_get_hit_type())
 * - stop type (message_get_stop_type())
 *
 * Does not guarantee that the actual samples (message_get_samples()) are
 * available (although they normally should be), this function only checks
 * the metadata listed above.
 */
int message_is_hit_aborted(const Message *m);
/**<
 * \return Non-zero if `m` is an aborted hit message.
 *
 * Indicates that the following data is available:
 * - channel ID (message_get_channel_id())
 * - info type (message_get_info_type()), can be #iDIS or #iMSB
 */
int message_is_buffer_overflow(const Message *m);
/**<
 * \return Non-zero if `m` is a buffer overflow message.
 *
 * Indicates that the following data is available:
 * - group ID (message_get_group_id())
 * - channel ID (message_get_channel_id())
 * - timestamp (message_get_timestamp())
 * - number of lost hits (message_get_buffer_overflow_count())
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
 * - info type (can only be #iSYN, so no need to check it)
 */
int message_is_info(const Message *m);
/**<
 * \return Non-zero if `m` is an info message
 *
 * Indicates that the following data is available:
 * - info type (message_get_info_type()), can be #iNGT, #iNRT, or #iNBE
 * - channel ID (message_get_channel_id()), if the info type is #iNGT or #iNBE
 */
/**@}*/

/**@{
 * \name Access message data
 * All functions in this section assume that `m` points to a
 * properly allocated and initialized message object (e.g. obtained from
 * message_new()).
 */
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
 * The number of available samples must be determined using
 * message_get_num_samples(). The memory containing the samples will be
 * released when `m` is destroyed by message_delete().
 */
uint8_t message_get_num_samples(const Message *m);
/**< \return The number of samples, if available, undefined otherwise. */
uint8_t message_get_hit_type(const Message *m);
/**< \return One of the #hit_types, if available, undefined otherwise. */
uint8_t message_get_stop_type(const Message *m);
/**< \return One of the #stop_types, if available, undefined otherwise. */
uint8_t message_get_buffer_overflow_count(const Message *m);
/**< \return The buffer overflow count, if available, undefined otherwise. */
uint16_t message_get_epoch_count(const Message *m);
/**< \return The epoch count, if available, undefined otherwise. */
uint8_t message_get_info_type(const Message *m);
/**< \return One of the #info_types, if available, undefined otherwise. */
/**@}*/

#ifdef __cplusplus
}
#endif
#endif

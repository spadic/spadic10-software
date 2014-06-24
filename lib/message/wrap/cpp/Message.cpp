#include "Message.h"

extern "C" {
#include "message.h"
}

namespace spadic {

Message::Message(_Message *m) : m(m), _samples_valid(false)
{
}

Message::~Message()
{
    message_delete(m);
}

//--------------------------------------------------------------------

bool Message::is_valid()
{
    return message_is_valid(m);
}

bool Message::is_hit()
{
    return message_is_hit(m);
}

bool Message::is_hit_aborted()
{
    return message_is_hit_aborted(m);
}

bool Message::is_buffer_overflow()
{
    return message_is_buffer_overflow(m);
}

bool Message::is_epoch_marker()
{
    return message_is_epoch_marker(m);
}

bool Message::is_epoch_out_of_sync()
{
    return message_is_epoch_out_of_sync(m);
}

bool Message::is_info()
{
    return message_is_info(m);
}

//--------------------------------------------------------------------

uint8_t Message::group_id()
{
    return message_get_group_id(m);
}

uint8_t Message::channel_id()
{
    return message_get_channel_id(m);
}

uint16_t Message::timestamp()
{
    return message_get_timestamp(m);
}

const std::vector<int16_t>& Message::samples()
{
    if (!_samples_valid) {
        int16_t *s;
        size_t n;
        if ((s = message_get_samples(m)) &&
            (n = message_get_num_samples(m))) {
            _samples.assign(s, s+n);
        }
        _samples_valid = true;
    }
    return _samples;
}

uint8_t Message::hit_type()
{
    return message_get_hit_type(m);
}

uint8_t Message::stop_type()
{
    return message_get_stop_type(m);
}

uint8_t Message::buffer_overflow_count()
{
    return message_get_buffer_overflow_count(m);
}

uint16_t Message::epoch_count()
{
    return message_get_epoch_count(m);
}

uint8_t Message::info_type()
{
    return message_get_info_type(m);
}

} // namespace

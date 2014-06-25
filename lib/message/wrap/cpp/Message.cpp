#include "Message.h"

extern "C" {
#include "message.h"
}

#define IS(NAME) bool is_##NAME() { return message_is_##NAME(m); }
#define GET(NAME) NAME() { return message_get_##NAME(m); }

namespace spadic {

struct Message_ : Message {
    IS (valid)
    IS (hit)
    IS (hit_aborted)
    IS (buffer_overflow)
    IS (epoch_marker)
    IS (epoch_out_of_sync)
    IS (info)

    uint8_t GET (group_id)
    uint8_t GET (channel_id)
    uint16_t GET (timestamp)
    const std::vector<int16_t>& samples() { return _samples; }
    uint8_t GET (hit_type)
    uint8_t GET (stop_type)
    uint8_t GET (buffer_overflow_count)
    uint16_t GET (epoch_count)
    uint8_t GET (info_type)

    Message_(struct message *m);
    ~Message_();

private:
    struct message *m;
    std::vector<int16_t> _samples;
    void init_samples();
};

Message_::Message_(struct message *m) : m(m)
{
    if (is_hit()) {
        init_samples();
    }
}

Message_::~Message_()
{
    message_delete(m);
}

void Message_::init_samples()
{
    int16_t *s;
    size_t n;
    if ((s = message_get_samples(m)) &&
        (n = message_get_num_samples(m))) {
        _samples.assign(s, s+n);
    }
}

#undef IS
#undef GET

} // namespace

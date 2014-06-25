#include "Message.h"

extern "C" {
#include "message.h"
#include "message_reader.h"
}

#define IS(NAME) bool is_##NAME() { return message_is_##NAME(m); }
#define GET(NAME) NAME() { return message_get_##NAME(m); }

typedef std::vector<int16_t> samples_t;
typedef std::vector<uint16_t> buf_t;

namespace spadic {

//-------------------------------------------------------------------

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
    const samples_t& samples() { return _samples; }
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

//-------------------------------------------------------------------

struct MessageReader_ : MessageReader {
    void reset() { message_reader_reset(r); };
    int add_buffer(uint16_t *buf, size_t len);
    const uint16_t *get_depleted() { return message_reader_get_depleted(r); };
    std::unique_ptr<Message> get_message();
    bool is_empty() { return message_reader_is_empty(r); };

    MessageReader_();
    ~MessageReader_();

private:
    struct message_reader *r;
};

MessageReader_::MessageReader_()
{
    r = message_reader_new();
}

MessageReader_::~MessageReader_()
{
    message_reader_delete(r);
}

int MessageReader_::add_buffer(uint16_t *buf, size_t len)
{
    return message_reader_add_buffer(r, buf, len);
}

std::unique_ptr<Message> MessageReader_::get_message()
{
    struct message *m = message_reader_get_message(r);
    Message_ *M = m ? new Message_(m) : nullptr;
    return std::unique_ptr<Message>(M);
}

//-------------------------------------------------------------------

std::unique_ptr<MessageReader> new_MessageReader()
{
    MessageReader_ *m = new MessageReader_;
    return std::unique_ptr<MessageReader_>(m);
}

} // namespace

#undef IS
#undef GET

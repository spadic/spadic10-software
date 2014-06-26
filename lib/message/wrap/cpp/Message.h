#ifndef SPADIC_MESSAGE_WRAP_H
#define SPADIC_MESSAGE_WRAP_H

#include <cstdint>
#include <memory>
#include <vector>

namespace spadic {

struct Message {
    virtual bool is_valid() = 0;
    virtual bool is_hit() = 0;
    virtual bool is_hit_aborted() = 0;
    virtual bool is_buffer_overflow() = 0;
    virtual bool is_epoch_marker() = 0;
    virtual bool is_epoch_out_of_sync() = 0;
    virtual bool is_info() = 0;

    virtual uint8_t group_id() = 0;
    virtual uint8_t channel_id() = 0;
    virtual uint16_t timestamp() = 0;
    virtual std::vector<int16_t> samples() = 0;
    virtual uint8_t hit_type() = 0;
    virtual uint8_t stop_type() = 0;
    virtual uint8_t buffer_overflow_count() = 0;
    virtual uint16_t epoch_count() = 0;
    virtual uint8_t info_type() = 0;

    virtual ~Message() {};
};

struct MessageReader {
    void reset();
    int add_buffer(uint16_t *buf, size_t len);
    const uint16_t *get_depleted();
    std::unique_ptr<Message> get_message();
    bool is_empty();

    ~MessageReader();
    MessageReader();

private:
    struct MessageReader_;
    std::unique_ptr<MessageReader_> r;
};

} // namespace

#endif

#ifndef SPADIC_MESSAGE_WRAP_H
#define SPADIC_MESSAGE_WRAP_H

#include <cstdint>
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
    virtual const std::vector<int16_t>& samples() = 0;
    virtual uint8_t hit_type() = 0;
    virtual uint8_t stop_type() = 0;
    virtual uint8_t buffer_overflow_count() = 0;
    virtual uint16_t epoch_count() = 0;
    virtual uint8_t info_type() = 0;

    virtual ~Message() {};
};

} // namespace

#endif

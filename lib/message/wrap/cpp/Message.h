#ifndef SPADIC_MESSAGE_WRAP_H
#define SPADIC_MESSAGE_WRAP_H

#include <vector>

extern "C" {
#include "message.h"
}

namespace SPADIC {

class Message {
public:
    Message(Message*);
    ~Message();

    bool is_valid();
    bool is_hit();
    bool is_hit_aborted();
    bool is_buffer_overflow();
    bool is_epoch_marker();
    bool is_epoch_out_of_sync();
    bool is_info();

    uint8_t group_id();
    uint8_t channel_id();
    uint16_t timestamp();
    std::vector<int16_t> samples();
    uint8_t hit_type();
    uint8_t stop_type();
    uint8_t buffer_overflow_count();
    uint16_t epoch_count();
    uint8_t info_type();

private:
    struct message *m;
};

} // namespace

#endif

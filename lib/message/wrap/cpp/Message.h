//! \author Michael Krieger
//! C++ API for the SPADIC Message library.

#ifndef SPADIC_MESSAGE_WRAP_H
#define SPADIC_MESSAGE_WRAP_H

#include <cstdint>
#include <memory>
#include <vector>

namespace spadic {

enum class stop_t : uint8_t {
#define STOP(X) X
#include "constants/stop_types.h"
#undef STOP
};
enum class info_t : uint8_t {
#define INFO(X) X
#include "constants/info_types.h"
#undef INFO
};
enum class hit_t : uint8_t {
#define HIT(X) X
#include "constants/hit_types.h"
#undef HIT
};

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
    virtual hit_t hit_type() = 0;
    virtual stop_t stop_type() = 0;
    virtual uint8_t buffer_overflow_count() = 0;
    virtual uint16_t epoch_count() = 0;
    virtual info_t info_type() = 0;

    virtual ~Message() {};
};

struct MessageReader {
    MessageReader();
    ~MessageReader();

    void reset();
    int add_buffer(const uint16_t *buf, size_t len);
    std::unique_ptr<Message> get_message();

    // TODO what to with these
    const uint16_t *get_depleted();
    bool is_empty();

private:
    struct MessageReader_;
    std::unique_ptr<MessageReader_> r;
};

} // namespace

#endif

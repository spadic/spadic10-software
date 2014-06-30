//! \author Michael Krieger
//! C++ API for the SPADIC Message library.
#ifndef SPADIC_MESSAGE_WRAP_H
#define SPADIC_MESSAGE_WRAP_H

#include <cstdint>
#include <memory>
#include <vector>

namespace spadic {

// wrap the hit/stop/info types using the technique shown in
// http://stackoverflow.com/a/20792525

enum class stop_t : uint8_t {
    END = 0x0, //!< Normal end of message
    EBF = 0x1, //!< Channel buffer full
    EFF = 0x2, //!< Ordering FIFO full
    EDH = 0x3, //!< Multi hit
    EDB = 0x4, //!< Multi hit and channel buffer full
    EDO = 0x5, //!< Multi hit and ordering FIFO full
  //XX1 = 0x6,
  //XX2 = 0x7,
};
enum class info_t : uint8_t {
    DIS = 0x0, //!< Channel disabled during message building
    NGT = 0x1, //!< Next grant timeout
    NRT = 0x2, //!< Next request timeout
    NBE = 0x3, //!< New grant but channel empty
    MSB = 0x4, //!< Corruption in message builder
    NOP = 0x5, //!< Empty word
    SYN = 0x6, //!< Epoch out of sync
  //XX3 = 0x7,
  //XX4 = 0x8,
  //XX5 = 0x9,
  //XX6 = 0xA,
  //XX7 = 0xB,
  //XX8 = 0xC,
  //XX9 = 0xD,
  //XXA = 0xE,
  //XXB = 0xF,
};
enum class hit_t : uint8_t {
    GLB = 0x0, //!< Global trigger
    SLF = 0x1, //!< Self triggered
    NBR = 0x2, //!< Neighbor triggered
    SAN = 0x3, //!< Self and neighbor triggered
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

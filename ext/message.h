#ifndef SPADIC_MESSAGE_H
#define SPADIC_MESSAGE_H
#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

struct Pattern {
    uint16_t value;
    uint16_t mask;
};

// preambles
static struct Pattern wSOM = {0x8000, 0xF000}; // start of message
static struct Pattern wTSW = {0x9000, 0xF000}; // time stamp
static struct Pattern wRDA = {0xA000, 0xF000}; // raw data
static struct Pattern wEOM = {0xB000, 0xF000}; // end of data message
static struct Pattern wBOM = {0xC000, 0xF000}; // buffer overflow count
static struct Pattern wEPM = {0xD000, 0xF000}; // epoch marker
static struct Pattern wEXD = {0xE000, 0xF000}; // extracted data
static struct Pattern wINF = {0xF000, 0xF000}; // information 
static struct Pattern wCON = {0x0000, 0x8000}; // continuation preamble

// stop types
static struct Pattern sEND = {0x0000, 0x0007};
static struct Pattern sEBF = {0x0001, 0x0007};
static struct Pattern sEFF = {0x0002, 0x0007};
static struct Pattern sEDH = {0x0003, 0x0007};
static struct Pattern sEDB = {0x0004, 0x0007};
static struct Pattern sEDO = {0x0005, 0x0007};
/* unused
static struct Pattern sXX1 = {0x0006, 0x0007};
static struct Pattern sXX2 = {0x0007, 0x0007};
*/

// info types (value, mask)
static struct Pattern iDIS = {0x0000, 0x0F00};
static struct Pattern iNGT = {0x0100, 0x0F00};
static struct Pattern iNRT = {0x0200, 0x0F00};
static struct Pattern iNBE = {0x0300, 0x0F00};
static struct Pattern iMSB = {0x0400, 0x0F00};
static struct Pattern iNOP = {0x0500, 0x0F00};
static struct Pattern iSYN = {0x0600, 0x0F00};
/* unused
static struct Pattern iXX3 = {0x0700, 0x0F00};
static struct Pattern iXX4 = {0x0800, 0x0F00};
static struct Pattern iXX5 = {0x0900, 0x0F00};
static struct Pattern iXX6 = {0x0A00, 0x0F00};
static struct Pattern iXX7 = {0x0B00, 0x0F00};
static struct Pattern iXX8 = {0x0C00, 0x0F00};
static struct Pattern iXX9 = {0x0D00, 0x0F00};
static struct Pattern iXXA = {0x0E00, 0x0F00};
static struct Pattern iXXB = {0x0F00, 0x0F00};
*/

// hit types
static struct Pattern hGLB = {0x0000, 0x0030};
static struct Pattern hSLF = {0x0010, 0x0030};
static struct Pattern hNBR = {0x0020, 0x0030};
static struct Pattern hSAN = {0x0030, 0x0030}; 

// functions
int match_word(uint16_t w, struct Pattern p);
uint16_t* seek_message_start(uint16_t* begin, uint16_t* end);
size_t seek_message_start_all(uint16_t* begin, uint16_t* end);
size_t seek_message_start_all_wrap(uint16_t* begin, size_t length);

#ifdef __cplusplus
}
#endif
#endif

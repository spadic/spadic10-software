#include <stdint.h>

struct Preamble {
    uint16_t value;
    uint16_t mask;
};

static const struct Preamble wSOM = {0x8000, 0xF000}; // start of message
static const struct Preamble wTSW = {0x9000, 0xF000}; // time stamp
static const struct Preamble wRDA = {0xA000, 0xF000}; // raw data
static const struct Preamble wEOM = {0xB000, 0xF000}; // end of data message
static const struct Preamble wBOM = {0xC000, 0xF000}; // buffer overflow count
static const struct Preamble wEPM = {0xD000, 0xF000}; // epoch marker
static const struct Preamble wEXD = {0xE000, 0xF000}; // extracted data
static const struct Preamble wINF = {0xF000, 0xF000}; // information 
static const struct Preamble wCON = {0x0000, 0x8000}; // continuation preamble

static int has_preamble(uint16_t w, struct Preamble p);


struct Field {
    uint16_t value;
    uint16_t mask;
};

// stop types
static struct Field sEND = {0x0000, 0x0007};
static struct Field sEBF = {0x0001, 0x0007};
static struct Field sEFF = {0x0002, 0x0007};
static struct Field sEDH = {0x0003, 0x0007};
static struct Field sEDB = {0x0004, 0x0007};
static struct Field sEDO = {0x0005, 0x0007};
/* unused
static struct Field sXX1 = {0x0006, 0x0007};
static struct Field sXX2 = {0x0007, 0x0007};
*/

// info types (value, mask)
static struct Field iDIS = {0x0000, 0x0F00};
static struct Field iNGT = {0x0100, 0x0F00};
static struct Field iNRT = {0x0200, 0x0F00};
static struct Field iNBE = {0x0300, 0x0F00};
static struct Field iMSB = {0x0400, 0x0F00};
static struct Field iNOP = {0x0500, 0x0F00};
static struct Field iSYN = {0x0600, 0x0F00};
/* unused
static struct Field iXX3 = {0x0700, 0x0F00};
static struct Field iXX4 = {0x0800, 0x0F00};
static struct Field iXX5 = {0x0900, 0x0F00};
static struct Field iXX6 = {0x0A00, 0x0F00};
static struct Field iXX7 = {0x0B00, 0x0F00};
static struct Field iXX8 = {0x0C00, 0x0F00};
static struct Field iXX9 = {0x0D00, 0x0F00};
static struct Field iXXA = {0x0E00, 0x0F00};
static struct Field iXXB = {0x0F00, 0x0F00};
*/

// hit types
static struct Field hGLB = {0x0000, 0x0030};
static struct Field hSLF = {0x0010, 0x0030};
static struct Field hNBR = {0x0020, 0x0030};
static struct Field hSAN = {0x0030, 0x0030};


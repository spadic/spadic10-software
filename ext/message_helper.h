/* Message */
struct _message {
    uint8_t group_id;
    uint8_t channel_id;
    uint16_t timestamp;
    uint16_t* data;
    uint8_t num_data;
    uint8_t hit_type;
    uint8_t stop_type;
    uint8_t buffer_overflow_count;
    uint16_t epoch_count;
    uint8_t info_type;

    uint8_t valid;
};

static void message_init(Message* m);
static void message_fill(Message* m, uint16_t w);

/* word types/preambles */
struct _wordtype {
    uint16_t value;
    uint16_t mask;
    uint8_t valid;
    void (fill*)(Message* m, uint16_t w);
} Wordtype;

static int word_is_type(uint16_t w, Wordtype t);
static Wordtype* word_get_type(uint16_t w);
static int word_is_ignore(uint16_t w);
static int word_is_start(uint16_t w);
static int word_is_end(uint16_t w);

static const Wordtype wSOM = {0x8000, 0xF000, 1<<0};
static const Wordtype wTSW = {0x9000, 0xF000, 1<<1};
static const Wordtype wRDA = {0xA000, 0xF000, 1<<2};
static const Wordtype wEOM = {0xB000, 0xF000, 1<<3};
static const Wordtype wBOM = {0xC000, 0xF000, 1<<4};
static const Wordtype wEPM = {0xD000, 0xF000, 1<<5};
static const Wordtype wEXD = {0xE000, 0xF000,    0};
static const Wordtype wINF = {0xF000, 0xF000, 1<<6};
static const Wordtype wCON = {0x0000, 0x8000,    0};

/* stop types */
static const uint8_t sEND = 0x0;
static const uint8_t sEBF = 0x1;
static const uint8_t sEFF = 0x2;
static const uint8_t sEDH = 0x3;
static const uint8_t sEDB = 0x4;
static const uint8_t sEDO = 0x5;
/* unused
static const uint8_t sXX1 = 0x6;
static const uint8_t sXX2 = 0x7;
*/

/* info types */
static const uint8_t iDIS = 0x0;
static const uint8_t iNGT = 0x1;
static const uint8_t iNRT = 0x2;
static const uint8_t iNBE = 0x3;
static const uint8_t iMSB = 0x4;
static const uint8_t iNOP = 0x5;
static const uint8_t iSYN = 0x6;
/* unused
static const uint8_t iXX3 = 0x7;
static const uint8_t iXX4 = 0x8;
static const uint8_t iXX5 = 0x9;
static const uint8_t iXX6 = 0xA;
static const uint8_t iXX7 = 0xB;
static const uint8_t iXX8 = 0xC;
static const uint8_t iXX9 = 0xD;
static const uint8_t iXXA = 0xE;
static const uint8_t iXXB = 0xF;
*/

/* hit types */
static const uint8_t hGLB = 0x0;
static const uint8_t hSLF = 0x1;
static const uint8_t hNBR = 0x2;
static const uint8_t hSAN = 0x3;

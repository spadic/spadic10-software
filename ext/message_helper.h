static void ptr_set_null(void *p);

/* Message */
struct _message {
    uint8_t group_id;
    uint8_t channel_id;
    uint16_t timestamp;
    uint16_t *samples;
    uint8_t num_samples;
    uint8_t hit_type;
    uint8_t stop_type;
    uint8_t buffer_overflow_count;
    uint16_t epoch_count;
    uint8_t info_type;

    uint8_t valid;

    /* up to 20 message words contain raw data */
    uint16_t (*raw_buf)[20];
    uint8_t raw_count;
};

static void message_init(Message *m);
static void message_fill(Message *m, uint16_t w);
static void fill_wSOM(Message *m, uint16_t w);
static void fill_wTSW(Message *m, uint16_t w);
static void fill_wRDA(Message *m, uint16_t w);
static void fill_wEOM(Message *m, uint16_t w);
static void fill_wBOM(Message *m, uint16_t w);
static void fill_wEPM(Message *m, uint16_t w);
static void fill_wEXD(Message *m, uint16_t w);
static void fill_wINF(Message *m, uint16_t w);
static void fill_wCON(Message *m, uint16_t w);

/* word types/preambles */
struct _wordtype {
    uint16_t value;
    uint16_t mask;
    uint8_t valid;
    void (*fill)(Message *m, uint16_t w);
} Wordtype;

static int word_is_type(uint16_t w, Wordtype t);
static Wordtype *word_get_type(uint16_t w);
static int word_is_ignore(uint16_t w);
static int word_is_start(uint16_t w);
static int word_is_end(uint16_t w);

static const Wordtype wSOM = {0x8000, 0xF000, 1<<0, fill_wSOM};
static const Wordtype wTSW = {0x9000, 0xF000, 1<<1, fill_wTSW};
static const Wordtype wRDA = {0xA000, 0xF000, 1<<2, fill_wRDA};
static const Wordtype wEOM = {0xB000, 0xF000, 1<<3, fill_wEOM};
static const Wordtype wBOM = {0xC000, 0xF000, 1<<4, fill_wBOM};
static const Wordtype wEPM = {0xD000, 0xF000, 1<<5, fill_wEPM};
static const Wordtype wEXD = {0xE000, 0xF000,    0, fill_wEXD};
static const Wordtype wINF = {0xF000, 0xF000, 1<<6, fill_wINF};
static const Wordtype wCON = {0x0000, 0x8000,    0, fill_wCON};

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
static uint8_t word_get_info_type(uint16_t w);

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

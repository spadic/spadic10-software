#include <iostream>
#include "Message.h"

int main()
{
    spadic::MessageReader r;

    uint16_t buf[8] = {
     0x8012, /* start of message 1 */
     0x9666,
     0xA008,
     0x0403,
     0x0100,
     0x5030,
     0x0E00,
     0xB1D0, /* end of message 1 */
    };

    r.add_buffer(buf, 8);

    auto m = r.get_message();
    auto s = m->samples();
    
    std::cout << "got " << s.size() << " samples" << std::endl;

    return 0;
}

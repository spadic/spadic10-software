#include <vector>
#include <iostream>
#include <iomanip>
#include <cstdint>

extern "C" {
size_t test_message_read(uint16_t* buf, size_t len);
}

std::vector<uint16_t> read_values(std::istream& input)
{
    uint16_t x;
    std::vector<uint16_t> result;
    while (input >> std::hex >> x) {
        result.push_back(x);
    }
    return result;
}

int main(int argc, char* argv[])
{
    std::vector<uint16_t> buf = read_values(std::cin);

    size_t n;
    n = test_message_read(buf.data(), buf.size());
    std::cout << "result: " << n << std::endl;
    
    return 0;
}

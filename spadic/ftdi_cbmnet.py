import Ftdi


# CBMnet port addresses
ADDR_DLM    = 0
ADDR_CTRL   = 1
ADDR_DATA_A = 2
ADDR_DATA_B = 3

# writable CBMnet ports and appropriate number of words
WRITE_LEN = {
  ADDR_DLM : 1,
  ADDR_CTRL: 3
}


class FtdiCbmnet(Ftdi.Ftdi):
    """Wrapper for FTDI <-> CBMnet interface communication."""


    def _cbmif_write(self, addr, words):
        """Write words to the CBMnet send interface."""

        if addr not in WRITE_LEN:
            raise ValueError("Cannot write to this CBMnet port.")
        if len(words) != WRITE_LEN[addr]:
            raise ValueError("Wrong number of words for this CBMnet port.")

        header = [addr, len(words)]
        data = []
        for w in words:
            high, low = w//0x100, w%0x100
            data.append(high)
            data.append(low)
        ftdi_data = header + data

        return self._ftdi_write(ftdi_data)//2


    def _cbmif_read(self):
        """Read words from the CBMnet receive interface."""

        header = self._ftdi_read(2, max_iter=10)
        if len(header) < 2:
            return None
        
        [addr, num_words] = header
        data = self._ftdi_read(2*num_words)
        words = []
        for i in range(num_words):
            high, low = data[2*i], data[2*i+1]
            w = (high<<8) + low
            words.append(w)

        return (addr, words)


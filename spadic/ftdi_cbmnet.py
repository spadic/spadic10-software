import Ftdi
import threading, Queue
import time


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

    def __init__(self):
        Ftdi.Ftdi.__init__(self)

        # set up write and read Queues
        self._write_queue = Queue.Queue()
        self._read_queue = Queue.Queue()

        # set up write/read Thread
        self._cbmif_thread = threading.Thread()
        self._cbmif_thread.run = self._cbmif_task
        self._cbmif_thread.daemon = True
        self._cbmif_thread.start()


    def _cbmif_write(self, addr, words):
        """Write words to the CBMnet send interface."""
        self._write_queue.put((addr, words))


    def _cbmif_ftdi_write(self, addr, words):
        """Access CBMnet send interface through FTDI write port.
        
        addr: Address of the CBMnet send port
        words: List of 16-bit words to be sent

        This method builds a data packet for the CBMnet send interface and
        transfers the individual bytes in the correct order through the
        FTDI write port.
        """
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
        while self._read_queue.empty():
            time.sleep(0.1)
        return self._read_queue.get()


    def _cbmif_ftdi_read(self):
        """Access CBMnet receive interface through FTDI read port.

        Returns a tuple (addr, words):
        addr: Address of the CBMnet receive port
        words: List of received 16-bit words

        This method reconstructs a data packet from the CBMnet receive
        interface out of the individual bytes from the FTDI read port.
        """
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


    def _cbmif_task(self):
        """Process write tasks and read all available data."""
        while True:
            while not self._write_queue.empty():
                (addr, words) = self._write_queue.get()
                self._cbmif_ftdi_write(addr, words)

            try:
                (addr, words) = self._cbmif_ftdi_read()
                self._read_queue.put((addr, words))
            except TypeError: # read result is None
                if self._write_queue.empty():
                    time.sleep(0.1)
                continue


import threading

#====================================================================
# generic representation of a single register and a register file
#====================================================================

class Register:
    """Representation of a single hardware register.
    
    Has a "staging area" for preparing the value that is to be written to
    the register and a "cache" for storing the last known value of the
    register, so that the number of hardware write and read operations can
    be minimized.
    """
    def __init__(self, address, size):
        """Set the address and size of the register."""
        self.addr = address
        self.size = size
        self._stage = 0     # staging area
        self._cache = None  # last known value of the hardware register
        self._known = False # is the current value of the hardware
                            # register known?


    def _write(self, addr, value):
        raise NotImplementedError(
            "Overwrite this with the hardware write operation.")

    def _read(self, addr):
        raise NotImplementedError(
            "Overwrite this with the hardware read operation.")


    def set(self, value):
        """Modify the staging area."""
        v = value % (2**self.size)
        if v != self._stage:
            self._stage = v

    def get(self):
        """Return the last known register value."""
        return self._stage


    def apply(self):
        """Perform the hardware write operation, if necessary.
        
        The write operation will transfer the value from the staging area
        to the hardware register. It is considered necessary if the last
        known value of the register differs from the staging area.

        After the write operation has been performed, the value of the
        hardware register will be considered "not known". It will become
        known again if the "update" or "read" methods are called.
        """
        if self._stage != self._cache:
            self._write(self.addr, self._stage)
            self._cache = self._stage
            self._known = False


    def update(self, blocking=True):
        """Perform the hardware read operation, if necessary.
        
        The read operation will transfer the value of the hardware
        register to the cache and the staging area. It is considered
        necessary if the value of the register is not known, which is the
        case
        - once initially, and
        - after each time the write operation has been performed by calling
          the "apply" or "write" methods.
        """
        if not self._known or self._stage != self._cache:
            t = threading.Thread()
            t.run = self._update_task
            t.name = "reg_%03X_reader" % self.addr
            t.start()
            if blocking:
                t.join()
            else:
                return t

    def _update_task(self):
        """Perform the hardware read operation."""
        try:
            result = self._read(self.addr)
        except IOError:
            return
        self._cache = result
        self._stage = self._cache
        self._known = True


    def write(self, value):
        """
        Modify the register value, if necessary perform the write operation.
        
        Has the same effect as calling "set" and then "apply".
        """
        self.set(value)
        self.apply()

    def read(self):
        """
        Return the register value, if necessary perform the read operation.
        
        Has the same effect as calling "update" and then "get".
        """
        self.update()
        return self.get()


class RegisterFile:
    """Representation of a generic register file."""

    def __init__(self, reg_map, write_method, read_method):
        """Set up all registers."""
        self._registers = {}
        for (name, (addr, size)) in reg_map.iteritems():
            r = Register(addr, size)
            r._write = write_method
            r._read = read_method
            self._registers[name] = r

        # emulate dictionary behaviour (read-only)
        self.__contains__ = self._registers.__contains__
        self.__iter__     = self._registers.__iter__
        self.__getitem__  = self._registers.__getitem__


    def set(self, config):
        """Load the staging area of the registers from a dictionary."""
        for name in config:
            self[name].set(config[name])

    def get(self):
        """Store the last known register values in a dictionary."""
        config = {}
        for name in self:
            config[name] = self[name].get()
        return config

    def apply(self):
        """Perform the write operation for all registers."""
        for name in self:
            self[name].apply()

    def update(self):
        """Perform the read operation for all registers."""
        last_unknown = 0
        fail_count = 0
        while True:
            unknown = [name for name in self if not self[name]._known]
            if len(unknown) != last_unknown:
                fail_count = 0
            else:
                fail_count += 1
            last_unknown = len(unknown)
            if not unknown or fail_count == 3:
                break
            # the code from here would be needed without the retransmit bug
            threads = []
            for name in unknown:
                t = self[name].update(blocking=False)
                if t is not None:
                    threads.append(t)
            for t in threads:
                t.join()
            # until here

    def write(self, config):
        """Write the register configuration contained in a dictionary.
        
        Has the same effect as calling "set" and then "apply".
        """
        self.set(config)
        self.apply()

    def read(self):
        """Read the register file configuration into a dictionary.
        
        Has the same effect as calling "update" and then "get".
        """
        self.update()
        return self.get()


#====================================================================
# representation of the SPADIC 1.0 register file
#====================================================================

#--------------------------------------------------------------------
# map of the user accessible registers
#--------------------------------------------------------------------
SPADIC_RF = {               # address, size
   "overrides"               : (  0x8,  7),
   "CbmNetAddr"              : ( 0x10, 16),
   "EpochCounter"            : ( 0x18, 16),
   "threshold1"              : ( 0x20,  9),
   "threshold2"              : ( 0x28,  9),
   "compDiffMode"            : ( 0x30,  1),
   "hitWindowLength"         : ( 0x38,  6),
   "selectMask_l"            : ( 0x40, 16),
   "selectMask_h"            : ( 0x48, 16),
   "bypassFilterStage"       : ( 0x50,  5),
   "aCoeffFilter_l"          : ( 0x58, 16),
   "aCoeffFilter_h"          : ( 0x60,  2),
   "bCoeffFilter_l"          : ( 0x68, 16),
   "bCoeffFilter_h"          : ( 0x70,  8),
   "scalingFilter"           : ( 0x78,  9),
   "offsetFilter"            : ( 0x80,  9),
   "groupIdA"                : ( 0x88,  8),
   "groupIdB"                : ( 0x90,  8),
#  "neighborSelectMatrixA_0" : ( 0x98, 16), # generated below
#  "neighborSelectMatrixA_1" : ( 0xA0, 16),
#  ...
#  "neighborSelectMatrixA_30": (0x188,  4),
#  "neighborSelectMatrixB_0" : (0x190, 16),
#  ...
#  "neighborSelectMatrixB_30": (0x280,  4),
   "disableChannelA"         : (0x288, 16),
   "disableChannelB"         : (0x290, 16),
   "disableEpochChannelA"    : (0x298,  1),
   "disableEpochChannelB"    : (0x2a0,  1),
   "enableTestOutput"        : (0x2a8,  1),
   "testOutputSelGroup"      : (0x2b0,  1),
   "enableTestInput"         : (0x2b8,  1),
   "enableAdcDec_l"          : (0x2c0, 16), # multiplex ADC signals to decoupling
   "enableAdcDec_h"          : (0x2c8,  5),
   "triggerMaskA"            : (0x2d0, 16), # enables DLM11 to trigger the hit logic
   "triggerMaskB"            : (0x2d8, 16),
   "enableAnalogTrigger"     : (0x2e0,  1), # enables DLM12 to inject an analog pulse into ch. 31
   "enableTriggerOutput"     : (0x2e8,  1), # enables DLM10 to generate the "TriggerOut" signal
}
  
# neighborSelectMatrix registers are generated here
for (group, base_addr) in [('A', 0x98), ('B', 0x190)]:
    for i in range(31): # 30*16 + 4 = 484
        name = 'neighborSelectMatrix%s_%i' % (group, i)
        addr = base_addr + 8*i
        SPADIC_RF[name] = (addr, (4 if i==30 else 16))


#--------------------------------------------------------------------
# inherit the generic register file class
#--------------------------------------------------------------------
class SpadicRegisterFile(RegisterFile):
    """Representation of the SPADIC register file."""
    def __init__(self, spadic):
        wr = spadic.write_register
        rd = spadic.read_register
        RegisterFile.__init__(self, SPADIC_RF, wr, rd)


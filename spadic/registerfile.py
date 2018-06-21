from collections.abc import Mapping
import threading

class RegisterReadFailure(IOError):
    pass

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
    def __init__(self, size, use_cache=True):
        """Set the size of the register."""
        self.size = size
        self._stage = 0     # staging area
        self._cache = None  # last known value of the hardware register
        self._known = False # is the current value of the hardware register known?
        self._use_cache = use_cache # enables the cache


    def _write(self, value):
        raise NotImplementedError(
            "Overwrite this with the appropriate write operation.")

    def _read(self):
        raise NotImplementedError(
            "Overwrite this with the appropriate read operation.")


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

        Regardless of whether it is considered necessary, the write
        operation will be performed if the "use_cache" option is False.

        After the write operation has been performed, the value of the
        hardware register will be considered "not known". It will become
        known again if the "update" or "read" methods are called.
        """
        if self._stage != self._cache:
            self._write(self._stage)
            if self._use_cache:
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

        Regardless of whether it is considered necessary, the read
        operation will be performed if the "use_cache" option is False.
        """
        if not self._known or self._stage != self._cache:
            t = threading.Thread()
            t.run = self._update_task
            t.start()
            if blocking:
                t.join()
            else:
                return t

    def _update_task(self):
        """Perform the hardware read operation."""
        try:
            result = self._read()
            if result is None:
                return
        except RegisterReadFailure:
            return # TODO do something better?
        self._stage = result
        if self._use_cache:
            self._cache = result
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


class RegisterFile(Mapping):
    """Representation of a generic register file."""

    def __init__(self, registers):
        """Set up all registers."""
        self._registers = registers

    # collections.abc.Mapping provides __contains__, keys, items, values, get,
    # __eq__, and __ne__
    def __getitem__(self, key):
        return self._registers.__getitem__(key)

    def __iter__(self):
        return self._registers.__iter__()

    def __len__(self):
        return self._registers.__len__()


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

    def update(self, blocking=False):
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
                t = self[name].update(blocking)
                if t is not None:
                    threads.append(t)
            for t in threads:
                t.join()
            # until here

    def write(self, config):
        """
        Write the register configuration contained in a dictionary.
        
        Has the same effect as calling "set" and then "apply".
        """
        self.set(config)
        self.apply()

    def read(self, blocking=False):
        """
        Read the register file configuration into a dictionary.
        
        Has the same effect as calling "update" and then "get".
        """
        self.update(blocking)
        return self.get()


#====================================================================
# representation of the SPADIC register file
#====================================================================

#--------------------------------------------------------------------
# map of the user accessible registers in SPADIC 1.x
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
# map of the user accessible registers in SPADIC 2.0
#--------------------------------------------------------------------
SPADIC20_RF = {             # address, size
   "overrides"               : (  0x8,  7),
   "readoutEnabled"          : ( 0x10,  1),
   "threshold1"              : ( 0x18,  9),
   "threshold2"              : ( 0x20,  9),
   "compDiffMode"            : ( 0x28,  1),
   "hitWindowLength"         : ( 0x30,  6),
   "selectMask_l"            : ( 0x38, 15),
   "selectMask_m"            : ( 0x40, 15),
   "selectMask_h"            : ( 0x48,  2),
   "bypassFilterStage"       : ( 0x50,  5),
   "aCoeffFilter_l"          : ( 0x58, 15),
   "aCoeffFilter_h"          : ( 0x60,  3),
   "bCoeffFilter_l"          : ( 0x68, 15),
   "bCoeffFilter_h"          : ( 0x70,  9),
   "scalingFilter"           : ( 0x78,  9),
   "offsetFilter"            : ( 0x80,  9),
   "groupIdA"                : ( 0x88,  8),
   "groupIdB"                : ( 0x90,  8),
#  "neighborSelectMatrixA_0" : ( 0x98, 15), # generated below
#  "neighborSelectMatrixA_1" : ( 0xA0, 15),
#  ...
#  "neighborSelectMatrixA_32": (0x198,  4),
#  "neighborSelectMatrixB_0" : (0x1a0, 15),
#  ...
#  "neighborSelectMatrixB_32": (0x2a0,  4),
   "disableChannelA_l"       : (0x2a8, 15),
   "disableChannelA_h"       : (0x2b0,  1),
   "disableChannelB_l"       : (0x2b8, 15),
   "disableChannelB_h"       : (0x2c0,  1),
   "disableEpochChannelA"    : (0x2c8,  1),
   "disableEpochChannelB"    : (0x2d0,  1),
   "enableTestOutput"        : (0x2d8,  1),
   "testOutputSelGroup"      : (0x2e0,  1),
   "enableTestInput"         : (0x2e8,  1),
   "enableAdcDec_l"          : (0x2f0, 15), # multiplex ADC signals to decoupling
   "enableAdcDec_h"          : (0x2f8,  6),
   "triggerMaskA_l"          : (0x300, 15), # enable triggering the hit logic
   "triggerMaskA_h"          : (0x308,  1),
   "triggerMaskB_l"          : (0x310, 15),
   "triggerMaskB_h"          : (0x318,  1),
   "enableAnalogTrigger"     : (0x320,  1), # enable injecting an analog pulse into ch. 31
   "enableTriggerOutput"     : (0x328,  1), # enable generating the "TriggerOut" signal
   "softReset"               : (0x330,  1),
   "CMD_trigger"             : (0x338,  2),
   "CMD_sync"                : (0x340,  1),
   "MON_status"              : (0x348,  1),
   # 0x350, 0x358, 0x360 -> shift register control
   "chipRevision"            : (0x368,  1)  # returns 0 for SPADIC 2.0 rev. 1, 1 for rev. 2
}

# neighborSelectMatrix registers are generated here
for (group, base_addr) in [('A', 0x98), ('B', 0x1a0)]:
    for i in range(33): # 32*15 + 4 = 484
        name = 'neighborSelectMatrix%s_%i' % (group, i)
        addr = base_addr + 8*i
        SPADIC20_RF[name] = (addr, (4 if i==32 else 15))


#--------------------------------------------------------------------
# inherit the generic register file class
#--------------------------------------------------------------------
class SpadicRegisterFile(RegisterFile):
    """Representation of the SPADIC register file."""

    def __init__(self, write_gen, read_gen, register_map, use_cache=True):
        """
        Set up the SPADIC registers.

        write_gen/read_gen must return functions that write/read the
        register with the given name or address.
        """
        registers = {}

        for (name, (addr, size)) in register_map.items():
            r = Register(size, use_cache)
            r._write = write_gen(name, addr)
            r._read = read_gen(name, addr)
            registers[name] = r

        RegisterFile.__init__(self, registers)


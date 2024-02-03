"""
Duck Machine model DM2022 CPU
"""

from instr_format import Instruction, OpCode, CondFlag, decode

from memory import Memory
from register import Register, ZeroRegister
from mvc import MVCEvent, MVCListenable
from typing import Tuple
import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class ALU(object):
    """The arithmetic logic unit (also called a "functional unit"
    in a modern CPU) executes a selected function but does not
    otherwise manage CPU state. A modern CPU core may have several
    ALUs to boost performance by performing multiple operatons
    in parallel, but the Duck Machine has just one ALU in one core.
    """
    # The ALU chooses one operation to apply based on a provided
    # operation code.  These are just simple functions of two arguments;
    # in hardware we would use a multiplexer circuit to connect the
    # inputs and output to the selected circuitry for each operation.
    ALU_OPS = {
        OpCode.ADD: lambda x, y: x + y,
        OpCode.SUB: lambda x, y: 0, # implement these opcodes
        OpCode.MUL: lambda x, y: 0,
        OpCode.DIV: lambda x, y: 0,
        # For memory access operations load, store, the ALU
        # performs the address calculation
        OpCode.LOAD: lambda x, y: x + y,
        OpCode.STORE: lambda x, y: x + y,
        # Some operations perform no operation
        OpCode.HALT: lambda x, y: 0
    }

    def exec(self, op: OpCode, in1: int, in2: int) -> Tuple[int, CondFlag]:
        pass # You must implement this method

class CPUStep(MVCEvent):
    """CPU is beginning step with PC at a given address"""
    def __init__(self, subject: "CPU", pc_addr: int,
                 instr_word: int, instr: Instruction)-> None:
        self.subject = subject
        self.pc_addr = pc_addr
        self.instr_word = instr_word
        self.instr = instr

class CPU(MVCListenable):
    """Duck Machine central processing unit (CPU)
    has 16 registers (including r0 that always holds zero
    and r15 that holds the program counter), a few
    flag registers (condition codes, halted state),
    and some logic for sequencing execution.  The CPU
    does not contain the main memory but has a bus connecting
    it to a separate memory.
    """

    def __init__(self, memory: Memory):
        super().__init__()
        self.memory = memory  # Not part of CPU; what we really have is a connection
        self.registers = [ ZeroRegister(), Register(), Register(), Register(),
                           Register(), Register(), Register(), Register(),
                           Register(), Register(), Register(), Register(),
                           Register(), Register(), Register(), Register() ]
        self.condition = CondFlag.ALWAYS
        self.halted = False
        self.alu = ALU()
        self.pc = self.registers[15]  # Alias to refer to program counter

    def step(self):
        """One fetch/decode/execute step"""
        # fetch - you must implement this part
        # Produce variables instr_addr and instr_word
        #
        # decode
        instr = decode(instr_word)
        # Convenient names for parts of instruction
        op = instr.op
        reg_target = instr.reg_target
        reg_left = instr.reg_src1
        reg_right = instr.reg_src2
        offset = instr.offset
        # Display the CPU state before executing instruction
        self.notify_all(CPUStep(self, instr_addr, instr_word, instr))
        # execute (conditionally)
        enabled = self.condition & instr.cond
        if enabled:
            result, flag  = self.alu.exec(
                instr.op,
                self.registers[reg_left].get(),
                self.registers[reg_right].get() + offset)
            self.condition = flag
            if self.condition == CondFlag.V:
                self.halted = True
            log.debug(f"ALU result of {instr.op}: {result}")
        self.pc.put(self.pc.get() + 1)
        if enabled:
            if op == OpCode.STORE:
                val = self.registers[reg_target].get()
                log.debug(f"Storing {val} from {reg_target} into address {result}")
                self.memory.put(result, val)
            elif instr.op == OpCode.LOAD:
                val = self.memory.get(result)
                log.debug(f"Loaded value {val} from {result}, saving to register {reg_target}")
                self.registers[reg_target].put(val)
            elif instr.op == OpCode.HALT:
                self.halted = True
            else:
                log.debug(f"R{reg_target} = {instr.op}(R{reg_left}, R{reg_right}+ {offset})")
                log.debug(f"Storing {result} into {reg_target}")
                self.registers[reg_target].put(result)

    def run(self, from_addr=0,  single_step=False) -> None:
        """fetc/decode/execute loop until we HALT"""
        self.halted = False
        self.registers[15].put(from_addr)
        step_count = 0
        while not self.halted:
            if single_step:
                input(f"Step {step_count}; press enter")
            self.step()
            step_count += 1



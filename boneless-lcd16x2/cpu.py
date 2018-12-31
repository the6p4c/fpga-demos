from boneless.arch.instr import *
from boneless.gateware.core_fsm import *
from nmigen import *
from nmigen.back import pysim
from nmigen.cli import main

from lcd import LCD

class CPU:
    def __init__(self):
        self.memory = Memory(width=16, depth=256)
        self.ext_port = LCD()

        def send_cmd(cmd):
            return [
                # Command: function set
                MOVL(R1, cmd),
                STX (R1, R0, 0),
                # Wait for busy flag to reset
                LDX (R1, R0, 0),
                CMP (R1, 0),
                JNZ (-3),
            ]
        
        self.memory.init = [
            *([0] * 8),
            *assemble([
                NOP (),
                NOP (),

                # Address for STX/LDX
                MOVL(R0, 0),

                # Command: function set
                *send_cmd(0b00111000),

                # Command: display on
                *send_cmd(0b00001110),

                # Command: entry mode set
                *send_cmd(0b00000110),

                # Command: clear display
                *send_cmd(0b00000001),

                # Print string
                # Address of string
                MOVL(R3, 44),

            'print_str',
                MOVH(R1, 1),
                LD  (R2, R3, 0),
                CMP (R2, 0),
                JE  ('halt'),

                OR  (R1, R1, R2),
                STX (R1, R0, 0),

                # Wait for busy flag to reset
                LDX (R1, R0, 0),
                CMP (R1, 0),
                JNZ (-3),

                ADDI(R3, 1),
                J   ('print_str'),

            'halt',
                J   ('halt'),

            'str',
            ]),
            *[ord(c) for c in 'Hello, boneless!'], 0
        ]

    def get_fragment(self, platform):
        m = Module()

        m.submodules.ext_port = self.ext_port

        m.submodules.mem_rdport = mem_rdport = self.memory.read_port(transparent=False)
        m.submodules.mem_wrport = mem_wrport = self.memory.write_port()
        m.submodules.core = BonelessCoreFSM(
            reset_addr=8,
            mem_rdport=mem_rdport,
            mem_wrport=mem_wrport,
            ext_port=self.ext_port
        )
        
        return m.lower(platform)

def simulate():
    uut = CPU()

    frag = uut.get_fragment(None)
    with pysim.Simulator(frag, vcd_file=open('cpu.vcd', 'w')) as sim:
        sim.add_clock(1 / 16e6, domain='sync')
        sim.run_until(1 / 16e6 * 10000, run_passive=True)

if __name__ == '__main__':
    #simulate()
    cpu = CPU()
    main(cpu, name='cpu', ports=[cpu.ext_port.db, cpu.ext_port.rs, cpu.ext_port.e])

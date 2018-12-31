from nmigen import *
from nmigen.back import pysim
from nmigen.cli import main

class LCD:
    def __init__(self):
        # LCD interface
        self.db = Signal(8, name='db')
        self.rs = Signal(name='rs')
        self.e = Signal(name='e')

        # boneless external port interface
        # Read address 0:
        #     Busy flag - 0 if ready, 1 if busy
        # Write address 0 (only valid if ready):
        #     RS and DB values
        #     0b0000000rdddddddd
        #     where: r = RS value, dddddddd = DB value
        self.addr = Signal(16)
        self.r_en = Signal()
        self.r_data = Signal(16)
        self.w_en = Signal()
        self.w_data = Signal(16)

    def get_fragment(self, platform):
        m = Module()

        busy = Signal()
        with m.If(self.addr == 0):
            with m.If(self.r_en):
                m.d.sync += self.r_data.eq(busy)
            with m.If(self.w_en & ~busy):
                m.d.sync += [
                    self.db.eq(self.w_data[0:8]),
                    self.rs.eq(self.w_data[8]),
                    busy.eq(1)
                ]

        # Following the datasheet seems to be a recipe for disaster
        # Use some very long setup/enable/hold/wait times (hundreds of us range)
        wait_counter = Signal(max=20000+1)
        with m.FSM(reset='WAIT_FOR_DATA'):
            with m.State('WAIT_FOR_DATA'):
                with m.If(busy):
                    m.next = 'SETUP'
            with m.State('SETUP'):
                m.d.sync += wait_counter.eq(wait_counter + 1)

                with m.If(wait_counter == 16):
                    m.d.sync += wait_counter.eq(0)
                    m.next = 'ENABLE'
            with m.State('ENABLE'):
                m.d.comb += self.e.eq(1)
                m.d.sync += wait_counter.eq(wait_counter + 1)

                with m.If(wait_counter == 5000):
                    m.d.sync += wait_counter.eq(0)
                    m.next = 'HOLD'
            with m.State('HOLD'):
                m.d.sync += wait_counter.eq(wait_counter + 1)

                with m.If(wait_counter == 16):
                    m.d.sync += wait_counter.eq(0)
                    m.next = 'WAIT_FOR_COMPLETE'
            with m.State('WAIT_FOR_COMPLETE'):
                m.d.sync += wait_counter.eq(wait_counter + 1)

                with m.If(wait_counter == 20000):
                    m.d.sync += [
                        wait_counter.eq(0),
                        busy.eq(0)
                    ]
                    m.next = 'WAIT_FOR_DATA'

        return m.lower(platform)

def simulate():
    uut = LCD()

    def testbench():
        def read(addr):
            # Set up address and read transaction
            yield uut.addr.eq(addr)
            yield uut.r_en.eq(1)
            # Wait one clock cycle for data
            yield
            yield uut.r_en.eq(0)
            return (yield uut.r_data)

        def write(addr, data):
            # Set up address and write transaction
            yield uut.addr.eq(addr)
            yield uut.w_data.eq(data)
            yield uut.w_en.eq(1)
            # Wait one clock cycle for write to complete
            yield
            yield uut.w_en.eq(0)

        def write_and_wait(rs, db):
            data = rs << 8 | db
            yield from write(0, data)
            while (yield from read(0)):
                pass

        data = [
            (0, 0b00111000),
            (0, 0b00001110),
            (0, 0b00000110),
            (0, 0b00000001),
            *[(1, ord(c)) for c in 'Hello, world!']
        ]

        yield
        for rs, db in data:
            yield from write_and_wait(rs, db)
        yield

    frag = uut.get_fragment(None)
    with pysim.Simulator(frag, vcd_file=open('lcd.vcd', 'w')) as sim:
        sim.add_clock(1 / 16e6, domain='sync')
        sim.add_sync_process(testbench(), domain='sync')
        sim.run()

if __name__ == '__main__':
    simulate()

    # lcd = LCD()
    # main(lcd, name='lcd', ports=[lcd.db, lcd.rs, lcd.e])

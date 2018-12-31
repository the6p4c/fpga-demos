from nmigen import *
from nmigen.cli import main

class LCD:
    def __init__(self):
        self.db = Signal(8, name='db')
        self.rs = Signal(name='rs')
        self.e = Signal(name='e')

    def get_fragment(self, platform):
        STR1 = '0123456789ABCDEF'
        STR2 = 'abcdefghijklmnop'
        data = [
            (0, 0b00111000), # function set (8 bit, 2 line, 5x8 dot char font)
            (0, 0b00001110), # display on
            (0, 0b00000110), # entry mode set (auto-increment address + cursor)
            (0, 0b00000001), # clear display
            *[(1, ord(c)) for c in STR1],
            (0, 0b11000000), # set ddram address (move to 2nd line)
            *[(1, ord(c)) for c in STR2]
        ]
        data_cmds = [x[1] for x in data]
        data_rss = [x[0] for x in data]

        idx = Signal(max=len(data))

        cmds = Array(data_cmds)
        rss = Array(data_rss)

        m = Module()

        m.d.comb += [
            self.db.eq(cmds[idx]),
            self.rs.eq(rss[idx])
        ]

        wait_counter = Signal(10)

        with m.FSM(reset='SETUP') as fsm:
            with m.State('SETUP'):
                m.d.comb += self.e.eq(0)
                m.next = 'HOLD'
            with m.State('HOLD'):
                m.d.comb += self.e.eq(1)
                m.d.sync += wait_counter.eq(0)
                m.next = 'WAIT'
            with m.State('WAIT'):
                m.d.comb += self.e.eq(0)
                m.d.sync += wait_counter.eq(wait_counter + 1)

                with m.If(wait_counter == 20):
                    m.d.sync += idx.eq(idx + 1)
                    with m.If(idx == len(data) - 1):
                        m.next = 'DONE'
                    with m.Else():
                        m.next = 'SETUP'

        return m.lower(platform)

if __name__ == '__main__':
    lcd = LCD()
    main(lcd, name='lcd', ports=[lcd.db, lcd.rs, lcd.e])

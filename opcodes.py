# opcodes.py
class Opcodes:
    def __init__(self):
        pass  # intentionally empty

    def nop(self, cpu):
        """
        NOP — No Operation
        Total cycles: 2 (1 already spent on fetch)
        """
        cpu.cycles += 1

    def lda_imm(self, cpu):
        """
        LDA #imm — Load Accumulator (Immediate)
        Total cycles: 2 (opcode fetch + operand fetch)
        """
        value = cpu.fetch_byte()   # operand fetch (1 cycle)
        cpu.A = value & 0xFF

        # Update flags
        # Zero flag (Z, bit 1)
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag (N, bit 7)
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

    def jmp_abs(self, cpu):
        """
        JMP abs — Jump Absolute
        Total cycles: 3 (opcode fetch + 2 operand fetches)
        """
        lo = cpu.fetch_byte()   # low byte
        hi = cpu.fetch_byte()   # high byte
        cpu.PC = ((hi << 8) | lo) & 0xFFFF
        cpu.cycles += 1

    def jmp_ind(self, cpu):
        """
        JMP (ind) — Jump Indirect
        Total cycles: 5
        Note: Includes 6502 page boundary bug
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        pointer = ((hi << 8) | lo) & 0xFFFF
        
        # 6502 bug: when pointer crosses page boundary, high byte is fetched from same page
        if (pointer & 0x00FF) == 0x00FF:
            # Bug: fetch low byte from pointer, high byte from pointer & 0xFF00
            addr_lo = cpu.bus.read(pointer)
            addr_hi = cpu.bus.read(pointer & 0xFF00)
        else:
            addr_lo = cpu.bus.read(pointer)
            addr_hi = cpu.bus.read(pointer + 1)
            
        cpu.PC = ((addr_hi << 8) | addr_lo) & 0xFFFF
        cpu.cycles += 2

    def sta_zp(self, cpu):
        """
        STA zp — Store Accumulator (Zero Page)
        Total cycles: 3 (opcode fetch + operand fetch + write)
        """
        addr = cpu.fetch_byte()        # zeropage address (1 cycle)
        cpu.bus.write(addr, cpu.A)     # write accumulator (1 cycle)
        cpu.cycles += 1

    def bne(self, cpu):
        """
        BNE — Branch if Not Equal
        Total cycles:
          - 2 base
          - +1 if branch taken
          - +1 if branch taken and page crossed
        """
        offset = cpu.fetch_byte()  # operand fetch (1 cycle)

        # Interpret offset as signed 8-bit
        if offset & 0x80:
            offset -= 0x100

        # Zero flag is bit 1 (0x02)
        z_flag_set = (cpu.P & 0x02) != 0
        if z_flag_set:
            # Branch not taken: nothing else to do
            return

        # Branch taken
        old_pc = cpu.PC
        cpu.PC = (cpu.PC + offset) & 0xFFFF
        cpu.cycles += 1  # taken branch penalty

        # Page-cross penalty
        if (old_pc & 0xFF00) != (cpu.PC & 0xFF00):
            cpu.cycles += 1

    def inx(self, cpu):
        """
        INX — Increment X Register
        Total cycles: 2 (opcode fetch + internal)
        """
        cpu.X = (cpu.X + 1) & 0xFF

        # Zero flag (Z, bit 1)
        if cpu.X == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag (N, bit 7)
        if cpu.X & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def cld(self, cpu):
        """
        CLD — Clear Decimal Mode
        Total cycles: 2 (opcode fetch + internal)
        """
        cpu.P &= ~0x08  # clear Decimal flag
        cpu.cycles += 1

    def sei(self, cpu):
        """
        SEI — Set Interrupt Disable
        Total cycles: 2 (opcode fetch + internal)
        """
        cpu.P |= 0x04   # set Interrupt Disable flag
        cpu.cycles += 1

    def ldx_imm(self, cpu):
        """
        LDX #imm — Load X Register (Immediate)
        Total cycles: 2 (opcode fetch + operand fetch)
        """
        value = cpu.fetch_byte()   # operand fetch (1 cycle)
        cpu.X = value & 0xFF

        # Zero flag (Z, bit 1)
        if cpu.X == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag (N, bit 7)
        if cpu.X & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

    def txs(self, cpu):
        """
        TXS — Transfer X to Stack Pointer
        Total cycles: 2 (opcode fetch + internal)
        """
        cpu.SP = cpu.X & 0xFF
        cpu.cycles += 1

    def txa(self, cpu):
        """
        TXA — Transfer X to Accumulator
        Total cycles: 2 (opcode fetch + internal)
        """
        cpu.A = cpu.X & 0xFF

        # Zero flag (Z, bit 1)
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag (N, bit 7)
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 1

    def sta_zpx(self, cpu):
        """
        STA zp,X — Store Accumulator (Zero Page,X)
        Total cycles: 4 (opcode fetch + operand fetch + internal + write)
        """
        base = cpu.fetch_byte()              # operand fetch (1 cycle)
        addr = (base + cpu.X) & 0xFF         # zeropage wraparound

        cpu.bus.write(addr, cpu.A)           # memory write (1 cycle)
        cpu.cycles += 2                      # internal calc + write cycle

    def sta_abs(self, cpu):
        """
        STA abs — Store Accumulator (Absolute)
        Total cycles: 4
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        addr = (hi << 8) | lo

        cpu.bus.write(addr, cpu.A)

        # Remaining cycle for memory write
        cpu.cycles += 1

    def sta_absx(self, cpu):
        """
        STA abs,X — Store Accumulator (Absolute,X)
        Total cycles: 5 (no page-cross penalty for stores)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.X) & 0xFFFF

        cpu.bus.write(addr, cpu.A)

        # No page-cross penalty for stores
        cpu.cycles += 2

    def sta_absy(self, cpu):
        """
        STA abs,Y — Store Accumulator (Absolute,Y)
        Total cycles: 5 (no page-cross penalty for stores)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.Y) & 0xFFFF

        cpu.bus.write(addr, cpu.A)

        cpu.cycles += 2

    def sta_indx(self, cpu):
        """
        STA (zp,X) — Store Accumulator (Indexed Indirect)
        Total cycles: 6
        """
        base = cpu.fetch_byte()
        zp = (base + cpu.X) & 0xFF

        lo = cpu.bus.read(zp)
        hi = cpu.bus.read((zp + 1) & 0xFF)
        addr = (hi << 8) | lo

        cpu.bus.write(addr, cpu.A)

        # Remaining cycles (address calc + write)
        cpu.cycles += 4

    def sta_indy(self, cpu):
        """
        STA (zp),Y — Store Accumulator (Indirect Indexed)
        Total cycles: 6 (no page-cross penalty for stores)
        """
        base = cpu.fetch_byte()
        lo = cpu.bus.read(base)
        hi = cpu.bus.read((base + 1) & 0xFF)
        base_addr = (hi << 8) | lo
        addr = (base_addr + cpu.Y) & 0xFFFF

        cpu.bus.write(addr, cpu.A)

        # No page-cross penalty for stores
        cpu.cycles += 4

    def asl_a(self, cpu):
        """
        ASL A — Arithmetic Shift Left (Accumulator)
        Total cycles: 2 (opcode fetch + internal)
        """
        # Capture bit 7 for Carry
        carry_out = (cpu.A >> 7) & 0x01

        # Shift left
        cpu.A = (cpu.A << 1) & 0xFF

        # Set/Clear Carry flag
        if carry_out:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        # Zero flag
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def asl_zp(self, cpu):
        """
        ASL zp — Arithmetic Shift Left (Zero Page)
        Total cycles: 5
        """
        addr = cpu.fetch_byte()
        value = cpu.bus.read(addr)

        carry_out = (value >> 7) & 0x01
        result = (value << 1) & 0xFF

        cpu.bus.write(addr, result)

        if carry_out:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 3

    def asl_abs(self, cpu):
        """
        ASL abs — Arithmetic Shift Left (Absolute)
        Total cycles: 6
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        addr = (hi << 8) | lo

        value = cpu.bus.read(addr)

        carry_out = (value >> 7) & 0x01
        result = (value << 1) & 0xFF

        cpu.bus.write(addr, result)

        if carry_out:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 3

    def asl_zpx(self, cpu):
        """
        ASL zp,X — Arithmetic Shift Left (Zero Page,X)
        Total cycles: 6
        """
        base = cpu.fetch_byte()
        addr = (base + cpu.X) & 0xFF

        value = cpu.bus.read(addr)

        carry_out = (value >> 7) & 0x01
        result = (value << 1) & 0xFF

        cpu.bus.write(addr, result)

        if carry_out:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 4

    def asl_absx(self, cpu):
        """
        ASL abs,X — Arithmetic Shift Left (Absolute,X)
        Total cycles: 7 (always 7, regardless of page crossing)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.X) & 0xFFFF

        value = cpu.bus.read(addr)

        carry_out = (value >> 7) & 0x01
        result = (value << 1) & 0xFF

        cpu.bus.write(addr, result)

        if carry_out:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 4

    def ora_abs(self, cpu):
        """
        ORA abs — Logical Inclusive OR (Absolute)
        Total cycles: 4 (opcode fetch + 2 operand fetch + read)
        """
        lo = cpu.fetch_byte()          # low byte (1 cycle)
        hi = cpu.fetch_byte()          # high byte (1 cycle)
        addr = ((hi << 8) | lo) & 0xFFFF

        value = cpu.bus.read(addr)     # memory read (1 cycle)

        cpu.A = (cpu.A | value) & 0xFF

        # Zero flag
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def dex(self, cpu):
        """
        DEX — Decrement X Register
        Total cycles: 2 (opcode fetch + internal)
        """
        cpu.X = (cpu.X - 1) & 0xFF

        # Zero flag (Z, bit 1)
        if cpu.X == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag (N, bit 7)
        if cpu.X & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 1

    def stx_zp(self, cpu):
        """
        STX zp — Store X Register (Zero Page)
        Total cycles: 3 (opcode fetch + operand fetch + write)
        """
        addr = cpu.fetch_byte()        # operand fetch (1 cycle)
        cpu.bus.write(addr, cpu.X)     # memory write (1 cycle)
        cpu.cycles += 1

    def jsr_abs(self, cpu):
        """
        JSR abs — Jump to Subroutine
        Total cycles: 6
        """
        # Fetch target address
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        target = (hi << 8) | lo

        # IMPORTANT:
        # PC has advanced past the operand fetches.
        # We must push (PC - 2), not (PC - 1)
        return_addr = (cpu.PC - 1) & 0xFFFF

        # Push high byte
        cpu.bus.write(0x0100 + cpu.SP, (return_addr >> 8) & 0xFF)
        cpu.SP = (cpu.SP - 1) & 0xFF

        # Push low byte
        cpu.bus.write(0x0100 + cpu.SP, return_addr & 0xFF)
        cpu.SP = (cpu.SP - 1) & 0xFF

        # Jump to subroutine
        cpu.PC = target

        # Remaining cycles (opcode fetch already counted)
        cpu.cycles += 3

    def lda_zp(self, cpu):
        """
        LDA zp — Load Accumulator (Zero Page)
        Total cycles: 3 (opcode fetch + operand fetch + read)
        """
        addr = cpu.fetch_byte()          # operand fetch (1 cycle)
        value = cpu.bus.read(addr)       # memory read (1 cycle)

        cpu.A = value & 0xFF

        # Zero flag (Z, bit 1)
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag (N, bit 7)
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def lda_abs(self, cpu):
        """
        LDA abs — Load Accumulator (Absolute)
        Total cycles: 4
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        addr = (hi << 8) | lo

        value = cpu.bus.read(addr)
        cpu.A = value & 0xFF

        # Zero flag
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def sec(self, cpu):
        """
        SEC — Set Carry Flag
        Total cycles: 2 (opcode fetch + internal)
        """
        cpu.P |= 0x01   # set Carry
        cpu.cycles += 1

    def sbc_imm(self, cpu):
        """
        SBC #imm — Subtract with Carry (Immediate)
        Total cycles: 2 (opcode fetch + operand fetch)
        Decimal mode ignored (6507 behavior)
        """
        value = cpu.fetch_byte()   # operand fetch (1 cycle)

        a = cpu.A
        c = 1 if (cpu.P & 0x01) else 0

        # Perform subtraction
        result = a - value - (1 - c)

        result8 = result & 0xFF
        cpu.A = result8

        # Carry flag: set if no borrow
        if result >= 0:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        # Zero flag
        if result8 == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if result8 & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Overflow flag
        if ((a ^ result8) & (a ^ value) & 0x80) != 0:
            cpu.P |= 0x40
        else:
            cpu.P &= ~0x40

    def bpl(self, cpu):
        """
        BPL — Branch if Plus (N == 0)
        Total cycles:
        - 2 base
        - +1 if branch taken
        - +1 if page crossed
        """
        offset = cpu.fetch_byte()

        if (cpu.P & 0x80) != 0:
            return  # branch not taken

        # sign-extend
        if offset & 0x80:
            offset -= 0x100

        old_pc = cpu.PC
        cpu.PC = (cpu.PC + offset) & 0xFFFF
        cpu.cycles += 1

        if (old_pc & 0xFF00) != (cpu.PC & 0xFF00):
            cpu.cycles += 1

    def and_imm(self, cpu):
        """
        AND #imm — Logical AND (Immediate)
        Total cycles: 2 (opcode fetch + operand fetch)
        """
        value = cpu.fetch_byte()   # operand fetch (1 cycle)

        cpu.A = cpu.A & value

        # Zero flag
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

    def clc(self, cpu):
        """
        CLC — Clear Carry Flag
        Total cycles: 2 (opcode fetch + internal)
        """
        cpu.P &= ~0x01   # clear Carry
        cpu.cycles += 1

    def adc_imm(self, cpu):
        """
        ADC #imm — Add with Carry (Immediate)
        Total cycles: 2 (opcode fetch + operand fetch)
        Decimal mode ignored (6507 behavior)
        """
        value = cpu.fetch_byte()   # operand fetch (1 cycle)

        a = cpu.A
        c = 1 if (cpu.P & 0x01) else 0

        result = a + value + c
        result8 = result & 0xFF

        cpu.A = result8

        # Carry flag
        if result > 0xFF:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        # Zero flag
        if result8 == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if result8 & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Overflow flag
        if (~(a ^ value) & (a ^ result8) & 0x80) != 0:
            cpu.P |= 0x40
        else:
            cpu.P &= ~0x40

    def ora_imm(self, cpu):
        """
        ORA #imm — Logical Inclusive OR (Immediate)
        Total cycles: 2 (opcode fetch + operand fetch)
        """
        value = cpu.fetch_byte()   # operand fetch (1 cycle)

        cpu.A = cpu.A | value

        # Zero flag
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

    def ldy_imm(self, cpu):
        """
        LDY #imm — Load Y Register (Immediate)
        Total cycles: 2 (opcode fetch + operand fetch)
        """
        value = cpu.fetch_byte()   # operand fetch (1 cycle)
        cpu.Y = value & 0xFF

        # Zero flag
        if cpu.Y == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.Y & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

    def sty_zpx(self, cpu):
        """
        STY zp,X — Store Y Register (Zero Page,X)
        Total cycles: 4 (opcode fetch + operand fetch + internal + write)
        """
        base = cpu.fetch_byte()              # operand fetch (1 cycle)
        addr = (base + cpu.X) & 0xFF         # zeropage wraparound

        cpu.bus.write(addr, cpu.Y)           # memory write (1 cycle)
        cpu.cycles += 2                      # internal calc + write

    def rts(self, cpu):
        if cpu.halted:
            return

        # pull low byte
        cpu.SP = (cpu.SP + 1) & 0xFF
        lo = cpu.bus.read(0x0100 + cpu.SP)
        # pull high byte
        cpu.SP = (cpu.SP + 1) & 0xFF
        hi = cpu.bus.read(0x0100 + cpu.SP)

        cpu.PC = ((hi << 8) | lo) + 1
        cpu.PC &= 0xFFFF

        cpu.cycles += 5

    def rti(self, cpu):
        """
        RTI — Return from Interrupt
        Total cycles: 6
        """
        if cpu.halted:
            return

        # Pull status register
        cpu.SP = (cpu.SP + 1) & 0xFF
        status = cpu.bus.read(0x0100 + cpu.SP)
        cpu.P = (status | 0x20) & 0xFF  # ensure unused bit stays set

        # Pull program counter
        cpu.SP = (cpu.SP + 1) & 0xFF
        lo = cpu.bus.read(0x0100 + cpu.SP)
        cpu.SP = (cpu.SP + 1) & 0xFF
        hi = cpu.bus.read(0x0100 + cpu.SP)

        cpu.PC = ((hi << 8) | lo) & 0xFFFF
        cpu.cycles += 5

    def brk(self, cpu):
        """
        BRK — Atari 2600 behavior
        No vectors, no stack push, just halt
        """
        cpu.cycles += 6
        cpu.PC = (cpu.PC + 1) & 0xFFFF  # absorb it

    def lda_absx(self, cpu):
        """
        LDA abs,X — Load Accumulator (Absolute,X)
        Total cycles: 4 (+1 if page crossed)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.X) & 0xFFFF

        value = cpu.bus.read(addr)
        cpu.A = value & 0xFF

        # Zero flag
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Page-cross penalty
        if (base & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1

    def lda_indx(self, cpu):
        """
        LDA (zp,X) — Load Accumulator (Indexed Indirect)
        Total cycles: 6
        """
        base = cpu.fetch_byte()
        zp = (base + cpu.X) & 0xFF

        lo = cpu.bus.read(zp)
        hi = cpu.bus.read((zp + 1) & 0xFF)
        addr = (hi << 8) | lo

        value = cpu.bus.read(addr)
        cpu.A = value & 0xFF

        # Zero flag
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 4

    def lda_indy(self, cpu):
        """
        LDA (zp),Y — Load Accumulator (Indirect Indexed)
        Total cycles: 5 (+1 if page crossed)
        """
        base = cpu.fetch_byte()
        lo = cpu.bus.read(base)
        hi = cpu.bus.read((base + 1) & 0xFF)
        base_addr = (hi << 8) | lo
        addr = (base_addr + cpu.Y) & 0xFFFF

        value = cpu.bus.read(addr)
        cpu.A = value & 0xFF

        # Zero flag
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 3

        # Page-cross penalty
        if (base_addr & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1

    def lsr_a(self, cpu):
        """
        LSR A — Logical Shift Right (Accumulator)
        Cycles: 2
        """

        # Carry gets old bit 0
        carry = cpu.A & 0x01

        # Shift right
        cpu.A = (cpu.A >> 1) & 0xFF

        # Update flags
        if carry:
            cpu.P |= 0x01      # C
        else:
            cpu.P &= ~0x01

        if cpu.A == 0:
            cpu.P |= 0x02      # Z
        else:
            cpu.P &= ~0x02

        cpu.P &= ~0x80         # N always cleared

        cpu.cycles += 1

    def lsr_zp(self, cpu):
        """
        LSR zp — Logical Shift Right (Zero Page)
        Total cycles: 5
        """
        addr = cpu.fetch_byte()        # operand fetch
        value = cpu.bus.read(addr)     # memory read

        carry = value & 0x01
        result = (value >> 1) & 0x7F

        cpu.bus.write(addr, result)    # write back

        if carry:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        cpu.P &= ~0x80               # N cleared

        # Remaining cycles: read + write + internal
        cpu.cycles += 3

    def lsr_abs(self, cpu):
        """
        LSR abs — Logical Shift Right (Absolute)
        Total cycles: 6
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        addr = (hi << 8) | lo

        value = cpu.bus.read(addr)

        carry = value & 0x01
        result = (value >> 1) & 0x7F

        cpu.bus.write(addr, result)

        if carry:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        cpu.P &= ~0x80

        # Remaining cycles: read + write + internal
        cpu.cycles += 3

    def ora_zpx(self, cpu):
        """
        ORA zp,X — Logical Inclusive OR (Zero Page,X)
        Total cycles: 4
        """
        base = cpu.fetch_byte()
        addr = (base + cpu.X) & 0xFF

        value = cpu.bus.read(addr)
        cpu.A = (cpu.A | value) & 0xFF

        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 2

    def ora_absx(self, cpu):
        """
        ORA abs,X — Logical Inclusive OR (Absolute,X)
        Total cycles: 4 (+1 if page crossed)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.X) & 0xFFFF

        value = cpu.bus.read(addr)
        cpu.A = (cpu.A | value) & 0xFF

        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        if (base & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1
        cpu.cycles += 1

    def ora_indx(self, cpu):
        """
        ORA (zp,X) — Logical Inclusive OR (Indexed Indirect)
        Total cycles: 6
        """
        base = cpu.fetch_byte()
        zp = (base + cpu.X) & 0xFF

        lo = cpu.bus.read(zp)
        hi = cpu.bus.read((zp + 1) & 0xFF)
        addr = (hi << 8) | lo

        value = cpu.bus.read(addr)
        cpu.A = (cpu.A | value) & 0xFF

        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Remaining cycles to reach 6 total
        cpu.cycles += 4

    def lsr_zpx(self, cpu):
        """
        LSR zp,X — Logical Shift Right (Zero Page,X)
        Total cycles: 6
        """
        base = cpu.fetch_byte()
        addr = (base + cpu.X) & 0xFF

        value = cpu.bus.read(addr)

        carry = value & 0x01
        result = (value >> 1) & 0x7F

        cpu.bus.write(addr, result)

        if carry:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        cpu.P &= ~0x80

        # Remaining cycles: index calc + read + write + internal
        cpu.cycles += 4

    def lsr_absx(self, cpu):
        """
        LSR abs,X — Logical Shift Right (Absolute,X)
        Total cycles: 7 (always 7, regardless of page crossing)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.X) & 0xFFFF

        value = cpu.bus.read(addr)

        carry = value & 0x01
        result = (value >> 1) & 0x7F

        cpu.bus.write(addr, result)

        if carry:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        cpu.P &= ~0x80

        # RMW abs,X is always 7 cycles, no extra page-cross penalty
        cpu.cycles += 4

    def pha(self, cpu):
        """
        PHA — Push Accumulator
        Total cycles: 3
        """
        # Push A onto stack
        cpu.bus.write(0x0100 + cpu.SP, cpu.A)
        cpu.SP = (cpu.SP - 1) & 0xFF

        # Remaining cycles (1 stack write + 1 internal)
        cpu.cycles += 2

    def pla(self, cpu):
        """
        PLA — Pull Accumulator
        Total cycles: 4
        """
        # Pull from stack
        cpu.SP = (cpu.SP + 1) & 0xFF
        value = cpu.bus.read(0x0100 + cpu.SP)

        cpu.A = value & 0xFF

        # Zero flag
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Remaining cycles:
        # 1 internal + 1 read + 1 internal = 3 extra
        cpu.cycles += 3

    def beq(self, cpu):
        """
        BEQ — Branch if Equal (Z == 1)
        """
        offset = cpu.fetch_byte()

        if cpu.P & 0x02:  # Z flag set
            if offset & 0x80:
                offset -= 0x100
            old_pc = cpu.PC
            cpu.PC = (cpu.PC + offset) & 0xFFFF
            cpu.cycles += 1

            if (old_pc & 0xFF00) != (cpu.PC & 0xFF00):
                cpu.cycles += 1

    def tya(self, cpu):
        """
        TYA — Transfer Y to Accumulator
        Total cycles: 2 (opcode fetch + internal)
        """
        cpu.A = cpu.Y & 0xFF

        # Zero flag
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 1

    def bmi(self, cpu):
        """
        BMI — Branch if Minus (N == 1)
        """
        offset = cpu.fetch_byte()   # operand fetch (1 cycle)

        # If Negative flag set
        if cpu.P & 0x80:
            # Sign-extend offset
            if offset & 0x80:
                offset -= 0x100

            old_pc = cpu.PC
            cpu.PC = (cpu.PC + offset) & 0xFFFF
            cpu.cycles += 1   # branch taken penalty

            if (old_pc & 0xFF00) != (cpu.PC & 0xFF00):
                cpu.cycles += 1

    def iny(self, cpu):
        """
        INY — Increment Y Register
        Total cycles: 2 (opcode fetch + internal)
        """
        cpu.Y = (cpu.Y + 1) & 0xFF

        # Zero flag
        if cpu.Y == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.Y & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 1

    def cmp_imm(self, cpu):
        value = cpu.fetch_byte()

        a = cpu.A
        result = (a - value) & 0xFF

        # Carry: set if A >= value
        if a >= value:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        # Zero
        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative
        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

    def bcs(self, cpu):
        """
        BCS — Branch if Carry Set (C == 1)
        """
        offset = cpu.fetch_byte()   # operand fetch (1 cycle)

        # If Carry flag NOT set → branch not taken
        if (cpu.P & 0x01) == 0:
            return

        # Sign-extend offset
        if offset & 0x80:
            offset -= 0x100

        old_pc = cpu.PC
        cpu.PC = (cpu.PC + offset) & 0xFFFF
        cpu.cycles += 1  # branch taken penalty

        # Optional page-cross penalty (you already do this elsewhere)
        if (old_pc & 0xFF00) != (cpu.PC & 0xFF00):
            cpu.cycles += 1

    def bcc(self, cpu):
        """
        BCC — Branch if Carry Clear (C == 0)
        """
        offset = cpu.fetch_byte()   # operand fetch (1 cycle)

        # If Carry flag is set → branch not taken
        if cpu.P & 0x01:
            return

        # Sign-extend offset
        if offset & 0x80:
            offset -= 0x100

        old_pc = cpu.PC
        cpu.PC = (cpu.PC + offset) & 0xFFFF
        cpu.cycles += 1  # branch taken penalty

        # Page-cross penalty
        if (old_pc & 0xFF00) != (cpu.PC & 0xFF00):
            cpu.cycles += 1

    def bvc(self, cpu):
        """
        BVC — Branch if Overflow Clear (V == 0)
        """
        offset = cpu.fetch_byte()

        if cpu.P & 0x40:
            return

        if offset & 0x80:
            offset -= 0x100

        old_pc = cpu.PC
        cpu.PC = (cpu.PC + offset) & 0xFFFF
        cpu.cycles += 1

        if (old_pc & 0xFF00) != (cpu.PC & 0xFF00):
            cpu.cycles += 1

    def bvs(self, cpu):
        """
        BVS — Branch if Overflow Set (V == 1)
        """
        offset = cpu.fetch_byte()

        if (cpu.P & 0x40) == 0:
            return

        if offset & 0x80:
            offset -= 0x100

        old_pc = cpu.PC
        cpu.PC = (cpu.PC + offset) & 0xFFFF
        cpu.cycles += 1

        if (old_pc & 0xFF00) != (cpu.PC & 0xFF00):
            cpu.cycles += 1

    def sty_zp(self, cpu):
        """
        STY zp — Store Y Register (Zero Page)
        Total cycles: 3
        """
        addr = cpu.fetch_byte()        # operand fetch (1 cycle)
        cpu.bus.write(addr, cpu.Y)     # memory write (1 cycle)
        cpu.cycles += 1

    def ldx_zp(self, cpu):
        """
        LDX zp — Load X Register (Zero Page)
        Total cycles: 3
        """
        addr = cpu.fetch_byte()        # operand fetch (1 cycle)
        value = cpu.bus.read(addr)     # memory read (1 cycle)

        cpu.X = value & 0xFF

        # Zero flag
        if cpu.X == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.X & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def ror_abs(self, cpu):
        """
        ROR abs — Rotate Right (Absolute)
        Total cycles: 6
        """
        lo = cpu.fetch_byte()     # low address byte
        hi = cpu.fetch_byte()     # high address byte
        addr = ((hi << 8) | lo) & 0xFFFF

        value = cpu.bus.read(addr)

        old_carry = cpu.P & 0x01
        new_carry = value & 0x01

        # Rotate right
        result = (value >> 1) & 0x7F
        if old_carry:
            result |= 0x80

        # Write back
        cpu.bus.write(addr, result)

        # Update Carry
        if new_carry:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        # Zero flag
        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Remaining cycles (read + write + internal)
        cpu.cycles += 3

    def ror_a(self, cpu):
        """
        ROR A — Rotate Right (Accumulator)
        Total cycles: 2
        """
        old_carry = cpu.P & 0x01
        new_carry = cpu.A & 0x01

        cpu.A = (cpu.A >> 1) & 0x7F
        if old_carry:
            cpu.A |= 0x80

        if new_carry:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 1

    def ror_zp(self, cpu):
        """
        ROR zp — Rotate Right (Zero Page)
        Total cycles: 5
        """
        addr = cpu.fetch_byte()
        value = cpu.bus.read(addr)

        old_carry = cpu.P & 0x01
        new_carry = value & 0x01

        result = (value >> 1) & 0x7F
        if old_carry:
            result |= 0x80

        cpu.bus.write(addr, result)

        if new_carry:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Remaining cycles: read + write + internal
        cpu.cycles += 3

    def ror_zpx(self, cpu):
        """
        ROR zp,X — Rotate Right (Zero Page,X)
        Total cycles: 6
        """
        base = cpu.fetch_byte()
        addr = (base + cpu.X) & 0xFF

        value = cpu.bus.read(addr)

        old_carry = cpu.P & 0x01
        new_carry = value & 0x01

        result = (value >> 1) & 0x7F
        if old_carry:
            result |= 0x80

        cpu.bus.write(addr, result)

        if new_carry:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Remaining cycles: index calc + read + write + internal
        cpu.cycles += 4

    def ror_absx(self, cpu):
        """
        ROR abs,X — Rotate Right (Absolute,X)
        Total cycles: 7 (always 7, regardless of page crossing)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.X) & 0xFFFF

        value = cpu.bus.read(addr)

        old_carry = cpu.P & 0x01
        new_carry = value & 0x01

        result = (value >> 1) & 0x7F
        if old_carry:
            result |= 0x80

        cpu.bus.write(addr, result)

        if new_carry:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # RMW abs,X is always 7 cycles, no extra page-cross penalty
        cpu.cycles += 4

    def sbc_absx(self, cpu):
        """
        SBC abs,X — Subtract with Carry (Absolute,X)
        Total cycles: 4 (+1 if page crossed)
        Decimal mode ignored (6507 behavior)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.X) & 0xFFFF

        value = cpu.bus.read(addr)

        a = cpu.A
        c = 1 if (cpu.P & 0x01) else 0

        result = a - value - (1 - c)
        result8 = result & 0xFF

        cpu.A = result8

        # Carry flag (no borrow)
        if result >= 0:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        # Zero flag
        if result8 == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if result8 & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Overflow flag
        if ((a ^ result8) & (a ^ value) & 0x80) != 0:
            cpu.P |= 0x40
        else:
            cpu.P &= ~0x40

        # Remaining base cycles (index calc + read)
        cpu.cycles += 2

        # Page-cross penalty
        if (base & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1

    def dec_zp(self, cpu):
        """
        DEC zp — Decrement Memory (Zero Page)
        Total cycles: 5
        """
        addr = cpu.fetch_byte()        # operand fetch (1 cycle)
        value = cpu.bus.read(addr)     # memory read (1 cycle)

        result = (value - 1) & 0xFF

        cpu.bus.write(addr, result)    # memory write (1 cycle)

        # Zero flag
        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Remaining cycles: read + write + internal
        cpu.cycles += 3

    def dec_zpx(self, cpu):
        """
        DEC zp,X — Decrement Memory (Zero Page,X)
        Total cycles: 6
        """
        base = cpu.fetch_byte()
        addr = (base + cpu.X) & 0xFF

        value = cpu.bus.read(addr)
        result = (value - 1) & 0xFF

        cpu.bus.write(addr, result)

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 4

    def cpx_imm(self, cpu):
        """
        CPX #imm — Compare X Register (Immediate)
        Total cycles: 2
        """
        value = cpu.fetch_byte()   # operand fetch (1 cycle)

        x = cpu.X
        result = (x - value) & 0xFF

        # Carry flag: set if X >= value
        if x >= value:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        # Zero flag
        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

    def eor_zp(self, cpu):
        """
        EOR zp — Exclusive OR (Zero Page)
        Total cycles: 3
        """
        addr = cpu.fetch_byte()        # operand fetch (1 cycle)
        value = cpu.bus.read(addr)     # memory read (1 cycle)

        cpu.A = (cpu.A ^ value) & 0xFF

        # Zero flag
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def eor_imm(self, cpu):
        """
        EOR #imm — Exclusive OR (Immediate)
        Total cycles: 2
        """
        value = cpu.fetch_byte()
        cpu.A = (cpu.A ^ value) & 0xFF

        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

    def eor_abs(self, cpu):
        """
        EOR abs — Exclusive OR (Absolute)
        Total cycles: 4
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        addr = (hi << 8) | lo

        value = cpu.bus.read(addr)
        cpu.A = (cpu.A ^ value) & 0xFF

        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def eor_absx(self, cpu):
        """
        EOR abs,X — Exclusive OR (Absolute,X)
        Total cycles: 4 (+1 if page crossed)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.X) & 0xFFFF

        value = cpu.bus.read(addr)
        cpu.A = (cpu.A ^ value) & 0xFF

        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        if (base & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1
        cpu.cycles += 1

    def eor_indx(self, cpu):
        """
        EOR (zp,X) — Exclusive OR (Indexed Indirect)
        Total cycles: 6
        """
        base = cpu.fetch_byte()
        zp = (base + cpu.X) & 0xFF

        lo = cpu.bus.read(zp)
        hi = cpu.bus.read((zp + 1) & 0xFF)
        addr = (hi << 8) | lo

        value = cpu.bus.read(addr)
        cpu.A = (cpu.A ^ value) & 0xFF

        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 4

    def eor_indy(self, cpu):
        """
        EOR (zp),Y — Exclusive OR (Indirect Indexed)
        Total cycles: 5 (+1 if page crossed)
        """
        base = cpu.fetch_byte()
        lo = cpu.bus.read(base)
        hi = cpu.bus.read((base + 1) & 0xFF)
        base_addr = (hi << 8) | lo
        addr = (base_addr + cpu.Y) & 0xFFFF

        value = cpu.bus.read(addr)
        cpu.A = (cpu.A ^ value) & 0xFF

        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 3

        if (base_addr & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1

    def rol_zp(self, cpu):
        """
        ROL zp — Rotate Left (Zero Page)
        Total cycles: 5
        """
        addr = cpu.fetch_byte()        # operand fetch (1 cycle)
        value = cpu.bus.read(addr)     # memory read (1 cycle)

        old_carry = 1 if (cpu.P & 0x01) else 0
        new_carry = (value >> 7) & 0x01

        # Rotate left
        result = ((value << 1) & 0xFF) | old_carry

        # Write back
        cpu.bus.write(addr, result)

        # Carry flag
        if new_carry:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        # Zero flag
        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Remaining cycles (read + write + internal)
        cpu.cycles += 3

    def sbc_zp(self, cpu):
        """
        SBC zp — Subtract with Carry (Zero Page)
        Total cycles: 3
        """
        addr = cpu.fetch_byte()        # operand fetch (1 cycle)
        value = cpu.bus.read(addr)     # memory read (1 cycle)

        a = cpu.A
        c = 1 if (cpu.P & 0x01) else 0

        result = a - value - (1 - c)
        result8 = result & 0xFF

        cpu.A = result8

        # Carry flag (no borrow)
        if result >= 0:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        # Zero flag
        if result8 == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if result8 & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Overflow flag
        if ((a ^ result8) & (a ^ value) & 0x80) != 0:
            cpu.P |= 0x40
        else:
            cpu.P &= ~0x40
        cpu.cycles += 1

    def sbc_zpx(self, cpu):
        """
        SBC zp,X — Subtract with Carry (Zero Page,X)
        Total cycles: 4
        """
        base = cpu.fetch_byte()
        addr = (base + cpu.X) & 0xFF

        value = cpu.bus.read(addr)

        a = cpu.A
        c = 1 if (cpu.P & 0x01) else 0

        result = a - value - (1 - c)
        result8 = result & 0xFF

        cpu.A = result8

        if result >= 0:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result8 == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result8 & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        if ((a ^ result8) & (a ^ value) & 0x80) != 0:
            cpu.P |= 0x40
        else:
            cpu.P &= ~0x40

        cpu.cycles += 2

    def tax(self, cpu):
        """
        TAX — Transfer Accumulator to X
        Total cycles: 2
        """
        cpu.X = cpu.A & 0xFF

        # Zero flag
        if cpu.X == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.X & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 1

    def ldy_zp(self, cpu):
        """
        LDY zp — Load Y Register (Zero Page)
        Total cycles: 3
        """
        addr = cpu.fetch_byte()        # operand fetch (1 cycle)
        value = cpu.bus.read(addr)     # memory read (1 cycle)

        cpu.Y = value & 0xFF

        # Zero flag
        if cpu.Y == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.Y & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def ldy_zpx(self, cpu):
        """
        LDY zp,X — Load Y Register (Zero Page,X)
        Total cycles: 4
        """
        base = cpu.fetch_byte()
        addr = (base + cpu.X) & 0xFF

        value = cpu.bus.read(addr)
        cpu.Y = value & 0xFF

        if cpu.Y == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.Y & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 2

    def lda_absy(self, cpu):
        """
        LDA abs,Y — Load Accumulator (Absolute,Y)
        Total cycles: 4 (+1 if page crossed)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.Y) & 0xFFFF

        value = cpu.bus.read(addr)
        cpu.A = value & 0xFF

        # Zero flag
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Page-cross penalty
        if (base & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1

    def ldx_zpy(self, cpu):
        """
        LDX zp,Y — Load X Register (Zero Page,Y)
        Total cycles: 4
        """
        base = cpu.fetch_byte()
        addr = (base + cpu.Y) & 0xFF

        value = cpu.bus.read(addr)
        cpu.X = value & 0xFF

        if cpu.X == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.X & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 2

    def cpy_imm(self, cpu):
        """
        CPY #imm — Compare Y Register (Immediate)
        Total cycles: 2
        """
        value = cpu.fetch_byte()   # operand fetch (1 cycle)

        y = cpu.Y
        result = (y - value) & 0xFF

        # Carry flag: set if Y >= value
        if y >= value:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        # Zero flag
        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

    def and_absx(self, cpu):
        """
        AND abs,X — Logical AND (Absolute,X)
        Total cycles: 4 (+1 if page crossed)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.X) & 0xFFFF

        value = cpu.bus.read(addr)
        cpu.A = (cpu.A & value) & 0xFF

        # Zero flag
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Page-cross penalty
        if (base & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1
        cpu.cycles += 1

    def and_absy(self, cpu):
        """
        AND abs,Y — Logical AND (Absolute,Y)
        Total cycles: 4 (+1 if page crossed)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.Y) & 0xFFFF

        value = cpu.bus.read(addr)
        cpu.A = (cpu.A & value) & 0xFF

        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        if (base & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1
        cpu.cycles += 1

    def and_zpx(self, cpu):
        """
        AND zp,X — Logical AND (Zero Page,X)
        Total cycles: 4
        """
        base = cpu.fetch_byte()
        addr = (base + cpu.X) & 0xFF

        value = cpu.bus.read(addr)
        cpu.A = (cpu.A & value) & 0xFF

        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 2

    def adc_zp(self, cpu):
        """
        ADC zp — Add with Carry (Zero Page)
        Total cycles: 3
        Decimal mode ignored (6507 behavior)
        """
        addr = cpu.fetch_byte()        # operand fetch (1 cycle)
        value = cpu.bus.read(addr)     # memory read (1 cycle)

        a = cpu.A
        c = 1 if (cpu.P & 0x01) else 0

        result = a + value + c
        result8 = result & 0xFF

        cpu.A = result8

        # Carry flag
        if result > 0xFF:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        # Zero flag
        if result8 == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if result8 & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Overflow flag
        if (~(a ^ value) & (a ^ result8) & 0x80) != 0:
            cpu.P |= 0x40
        else:
            cpu.P &= ~0x40
        cpu.cycles += 1

    def adc_abs(self, cpu):
        """
        ADC abs — Add with Carry (Absolute)
        Total cycles: 4
        Decimal mode ignored (6507 behavior)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        addr = (hi << 8) | lo

        value = cpu.bus.read(addr)

        a = cpu.A
        c = 1 if (cpu.P & 0x01) else 0

        result = a + value + c
        result8 = result & 0xFF

        cpu.A = result8

        # Carry flag
        if result > 0xFF:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        # Zero flag
        if result8 == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if result8 & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Overflow flag
        if (~(a ^ value) & (a ^ result8) & 0x80) != 0:
            cpu.P |= 0x40
        else:
            cpu.P &= ~0x40
        cpu.cycles += 1

    def adc_zpx(self, cpu):
        """
        ADC zp,X — Add with Carry (Zero Page,X)
        Total cycles: 4
        Decimal mode ignored (6507 behavior)
        """
        base = cpu.fetch_byte()
        addr = (base + cpu.X) & 0xFF

        value = cpu.bus.read(addr)

        a = cpu.A
        c = 1 if (cpu.P & 0x01) else 0

        result = a + value + c
        result8 = result & 0xFF

        cpu.A = result8

        if result > 0xFF:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result8 == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result8 & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        if (~(a ^ value) & (a ^ result8) & 0x80) != 0:
            cpu.P |= 0x40
        else:
            cpu.P &= ~0x40
        cpu.cycles += 2

    def adc_absx(self, cpu):
        """
        ADC abs,X — Add with Carry (Absolute,X)
        Total cycles: 4 (+1 if page crossed)
        Decimal mode ignored (6507 behavior)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.X) & 0xFFFF

        value = cpu.bus.read(addr)

        a = cpu.A
        c = 1 if (cpu.P & 0x01) else 0

        result = a + value + c
        result8 = result & 0xFF

        cpu.A = result8

        if result > 0xFF:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result8 == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result8 & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        if (~(a ^ value) & (a ^ result8) & 0x80) != 0:
            cpu.P |= 0x40
        else:
            cpu.P &= ~0x40

        cpu.cycles += 1

        if (base & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1

    def adc_absy(self, cpu):
        """
        ADC abs,Y — Add with Carry (Absolute,Y)
        Total cycles: 4 (+1 if page crossed)
        Decimal mode ignored (6507 behavior)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.Y) & 0xFFFF

        value = cpu.bus.read(addr)

        a = cpu.A
        c = 1 if (cpu.P & 0x01) else 0

        result = a + value + c
        result8 = result & 0xFF

        cpu.A = result8

        if result > 0xFF:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result8 == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result8 & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        if (~(a ^ value) & (a ^ result8) & 0x80) != 0:
            cpu.P |= 0x40
        else:
            cpu.P &= ~0x40

        cpu.cycles += 1

        if (base & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1

    def adc_indx(self, cpu):
        """
        ADC (zp,X) — Add with Carry (Indexed Indirect)
        Total cycles: 6
        Decimal mode ignored (6507 behavior)
        """
        base = cpu.fetch_byte()
        zp = (base + cpu.X) & 0xFF

        lo = cpu.bus.read(zp)
        hi = cpu.bus.read((zp + 1) & 0xFF)
        addr = (hi << 8) | lo

        value = cpu.bus.read(addr)

        a = cpu.A
        c = 1 if (cpu.P & 0x01) else 0

        result = a + value + c
        result8 = result & 0xFF

        cpu.A = result8

        if result > 0xFF:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result8 == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result8 & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        if (~(a ^ value) & (a ^ result8) & 0x80) != 0:
            cpu.P |= 0x40
        else:
            cpu.P &= ~0x40
        cpu.cycles += 4

    def adc_indy(self, cpu):
        """
        ADC (zp),Y — Add with Carry (Indirect Indexed)
        Total cycles: 5 (+1 if page crossed)
        Decimal mode ignored (6507 behavior)
        """
        base = cpu.fetch_byte()
        lo = cpu.bus.read(base)
        hi = cpu.bus.read((base + 1) & 0xFF)
        base_addr = (hi << 8) | lo
        addr = (base_addr + cpu.Y) & 0xFFFF

        value = cpu.bus.read(addr)

        a = cpu.A
        c = 1 if (cpu.P & 0x01) else 0

        result = a + value + c
        result8 = result & 0xFF

        cpu.A = result8

        if result > 0xFF:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result8 == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result8 & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        if (~(a ^ value) & (a ^ result8) & 0x80) != 0:
            cpu.P |= 0x40
        else:
            cpu.P &= ~0x40

        cpu.cycles += 3

        if (base_addr & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1

    def tay(self, cpu):
        """
        TAY — Transfer Accumulator to Y
        Total cycles: 2
        """
        cpu.Y = cpu.A & 0xFF

        # Zero flag
        if cpu.Y == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.Y & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 1

    def lda_zpx(self, cpu):
        """
        LDA zp,X — Load Accumulator (Zero Page,X)
        Total cycles: 4
        """
        base = cpu.fetch_byte()            # operand fetch (1 cycle)
        addr = (base + cpu.X) & 0xFF       # zeropage wraparound

        value = cpu.bus.read(addr)         # memory read (1 cycle)
        cpu.A = value & 0xFF

        # Zero flag
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Remaining cycles (index calc + read)
        cpu.cycles += 2

    def and_zp(self, cpu):
        """
        AND zp — Logical AND (Zero Page)
        Total cycles: 3
        """
        addr = cpu.fetch_byte()        # operand fetch (1 cycle)
        value = cpu.bus.read(addr)     # memory read (1 cycle)

        cpu.A = (cpu.A & value) & 0xFF

        # Zero flag
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def and_abs(self, cpu):
        """
        AND abs — Logical AND (Absolute)
        Total cycles: 4
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        addr = (hi << 8) | lo

        value = cpu.bus.read(addr)
        cpu.A = (cpu.A & value) & 0xFF

        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def and_indx(self, cpu):
        """
        AND (zp,X) — Logical AND (Indexed Indirect)
        Total cycles: 6
        """
        base = cpu.fetch_byte()              # operand fetch
        zp = (base + cpu.X) & 0xFF           # zeropage wrap

        lo = cpu.bus.read(zp)
        hi = cpu.bus.read((zp + 1) & 0xFF)
        addr = (hi << 8) | lo

        value = cpu.bus.read(addr)
        cpu.A = (cpu.A & value) & 0xFF

        # Zero flag
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Remaining internal cycles
        cpu.cycles += 4

    def and_indy(self, cpu):
        """
        AND (zp),Y — Logical AND (Indirect Indexed)
        Total cycles: 5 (+1 if page crossed)
        """
        base = cpu.fetch_byte()
        lo = cpu.bus.read(base)
        hi = cpu.bus.read((base + 1) & 0xFF)
        base_addr = (hi << 8) | lo
        addr = (base_addr + cpu.Y) & 0xFFFF

        value = cpu.bus.read(addr)
        cpu.A = (cpu.A & value) & 0xFF

        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 3

        if (base_addr & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1

    def cmp_zpx(self, cpu):
        """
        CMP zp,X — Compare Accumulator (Zero Page,X)
        Total cycles: 4
        """
        base = cpu.fetch_byte()
        addr = (base + cpu.X) & 0xFF

        value = cpu.bus.read(addr)
        result = (cpu.A - value) & 0xFF

        if cpu.A >= value:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 2

    def cmp_absy(self, cpu):
        """
        CMP abs,Y — Compare Accumulator (Absolute,Y)
        Total cycles: 4 (+1 if page crossed)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.Y) & 0xFFFF

        value = cpu.bus.read(addr)
        result = (cpu.A - value) & 0xFF

        if cpu.A >= value:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 1

        if (base & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1

    def clv(self, cpu):
        """
        CLV — Clear Overflow Flag
        Total cycles: 2
        """
        cpu.P &= ~0x40
        cpu.cycles += 1

    def sed(self, cpu):
        """
        SED — Set Decimal Flag
        Total cycles: 2
        Note: Decimal mode is ignored on 6507 (Atari 2600)
        """
        cpu.P |= 0x08
        cpu.cycles += 1

    def ill_nop_absx(self, cpu):
        """
        Illegal opcode FC — NOP abs,X
        Undocumented NMOS 6507 behavior
        Total cycles: 4 (+1 if page crossed)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.X) & 0xFFFF

        # Page-cross penalty
        if (base & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1

        # Remaining internal cycles
        cpu.cycles += 2

    def ill_isc_absx(self, cpu):
        """
        Illegal opcode FF — ISC abs,X
        INC memory, then SBC memory
        Total cycles: 7 (always 7, regardless of page crossing)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.X) & 0xFFFF

        # --- INC abs,X (read-modify-write) ---
        value = cpu.bus.read(addr)
        value = (value + 1) & 0xFF
        cpu.bus.write(addr, value)

        # --- SBC with updated memory value ---
        a = cpu.A
        c = 1 if (cpu.P & 0x01) else 0

        result = a - value - (1 - c)
        result8 = result & 0xFF
        cpu.A = result8

        # Carry flag (no borrow)
        if result >= 0:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        # Zero flag
        if result8 == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if result8 & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Overflow flag
        if ((a ^ result8) & (a ^ value) & 0x80) != 0:
            cpu.P |= 0x40
        else:
            cpu.P &= ~0x40

        # RMW abs,X is always 7 cycles, no extra page-cross penalty
        cpu.cycles += 4

    def ora_zp(self, cpu):
        """
        ORA zp — Logical Inclusive OR (Zero Page)
        Total cycles: 3
        """
        addr = cpu.fetch_byte()        # operand fetch (1 cycle)
        value = cpu.bus.read(addr)     # memory read (1 cycle)

        cpu.A = (cpu.A | value) & 0xFF

        # Zero flag
        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def inc_zpx(self, cpu):
        """
        INC zp,X — Increment Memory (Zero Page,X)
        Total cycles: 6
        """
        base = cpu.fetch_byte()            # operand fetch (1 cycle)
        addr = (base + cpu.X) & 0xFF       # zeropage wraparound

        value = cpu.bus.read(addr)         # memory read (1 cycle)
        result = (value + 1) & 0xFF

        cpu.bus.write(addr, result)        # memory write (1 cycle)

        # Zero flag
        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Remaining cycles (index calc + RMW internal)
        cpu.cycles += 4

    def ill_dcp_zp(self, cpu):
        """
        Illegal opcode C7 — DCP zp
        DEC memory, then CMP memory
        Total cycles: 5
        """
        addr = cpu.fetch_byte()          # operand fetch (1 cycle)

        # --- DEC zp ---
        value = cpu.bus.read(addr)
        value = (value - 1) & 0xFF
        cpu.bus.write(addr, value)

        # --- CMP A with value ---
        a = cpu.A
        result = (a - value) & 0xFF

        # Carry flag: set if A >= value
        if a >= value:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        # Zero flag
        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # Remaining cycles (DEC + CMP internals)
        cpu.cycles += 3

    def ill_kil(self, cpu):
        """
        Illegal opcode 62 — KIL / JAM
        Halts the CPU permanently until reset
        """
        cpu.halted = True
        cpu.cycles += 1

    def dey(self, cpu):
        """
        DEY — Decrement Y Register
        Total cycles: 2 (opcode fetch + internal)
        """
        cpu.Y = (cpu.Y - 1) & 0xFF

        # Zero flag
        if cpu.Y == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        # Negative flag
        if cpu.Y & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 1

    def tsx(self, cpu):
        """
        TSX — Transfer Stack Pointer to X
        Total cycles: 2
        """
        cpu.X = cpu.SP & 0xFF

        if cpu.X == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.X & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def php(self, cpu):
        """
        PHP — Push Processor Status
        Total cycles: 3
        """
        value = cpu.P | 0x30  # set B and unused bits when pushing
        cpu.bus.write(0x0100 + cpu.SP, value)
        cpu.SP = (cpu.SP - 1) & 0xFF
        cpu.cycles += 2

    def plp(self, cpu):
        """
        PLP — Pull Processor Status
        Total cycles: 4
        """
        cpu.SP = (cpu.SP + 1) & 0xFF
        value = cpu.bus.read(0x0100 + cpu.SP)
        cpu.P = (value | 0x20) & 0xFF  # ensure unused bit stays set
        cpu.cycles += 3

    def bit_zp(self, cpu):
        """
        BIT zp — Bit Test (Zero Page)
        Total cycles: 3
        """
        addr = cpu.fetch_byte()
        value = cpu.bus.read(addr)

        cpu.P &= ~0x02  # clear Z
        if (cpu.A & value) == 0:
            cpu.P |= 0x02

        # Set N from bit 7, V from bit 6
        cpu.P = (cpu.P & ~0xC0) | (value & 0xC0)
        cpu.cycles += 1

    def bit_abs(self, cpu):
        """
        BIT abs — Bit Test (Absolute)
        Total cycles: 4
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        addr = (hi << 8) | lo
        value = cpu.bus.read(addr)

        cpu.P &= ~0x02
        if (cpu.A & value) == 0:
            cpu.P |= 0x02

        cpu.P = (cpu.P & ~0xC0) | (value & 0xC0)
        cpu.cycles += 1

    def rol_a(self, cpu):
        """
        ROL A — Rotate Left (Accumulator)
        Total cycles: 2
        """
        old_carry = 1 if (cpu.P & 0x01) else 0
        new_carry = (cpu.A >> 7) & 0x01

        cpu.A = ((cpu.A << 1) & 0xFF) | old_carry

        if new_carry:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 1

    def rol_zp(self, cpu):
        """
        ROL zp — Rotate Left (Zero Page)
        Total cycles: 5
        """
        addr = cpu.fetch_byte()
        value = cpu.bus.read(addr)

        old_carry = 1 if (cpu.P & 0x01) else 0
        new_carry = (value >> 7) & 0x01

        result = ((value << 1) & 0xFF) | old_carry
        cpu.bus.write(addr, result)

        if new_carry:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 3

    def rol_abs(self, cpu):
        """
        ROL abs — Rotate Left (Absolute)
        Total cycles: 6
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        addr = (hi << 8) | lo

        value = cpu.bus.read(addr)

        old_carry = 1 if (cpu.P & 0x01) else 0
        new_carry = (value >> 7) & 0x01

        result = ((value << 1) & 0xFF) | old_carry
        cpu.bus.write(addr, result)

        if new_carry:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 3

    def rol_zpx(self, cpu):
        """
        ROL zp,X — Rotate Left (Zero Page,X)
        Total cycles: 6
        """
        base = cpu.fetch_byte()
        addr = (base + cpu.X) & 0xFF

        value = cpu.bus.read(addr)
        old_carry = 1 if (cpu.P & 0x01) else 0
        new_carry = (value >> 7) & 0x01

        result = ((value << 1) & 0xFF) | old_carry
        cpu.bus.write(addr, result)

        if new_carry:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 4

    def rol_absx(self, cpu):
        """
        ROL abs,X — Rotate Left (Absolute,X)
        Total cycles: 7 (always 7, regardless of page crossing)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.X) & 0xFFFF

        value = cpu.bus.read(addr)
        old_carry = 1 if (cpu.P & 0x01) else 0
        new_carry = (value >> 7) & 0x01

        result = ((value << 1) & 0xFF) | old_carry
        cpu.bus.write(addr, result)

        if new_carry:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # RMW abs,X is always 7 cycles, no extra page-cross penalty
        cpu.cycles += 4

    def inc_zp(self, cpu):
        """
        INC zp — Increment Memory (Zero Page)
        Total cycles: 5
        """
        addr = cpu.fetch_byte()
        value = cpu.bus.read(addr)
        result = (value + 1) & 0xFF
        cpu.bus.write(addr, result)

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 3

    def inc_abs(self, cpu):
        """
        INC abs — Increment Memory (Absolute)
        Total cycles: 6
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        addr = (hi << 8) | lo
        value = cpu.bus.read(addr)
        result = (value + 1) & 0xFF
        cpu.bus.write(addr, result)

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 3

    def inc_absx(self, cpu):
        """
        INC abs,X — Increment Memory (Absolute,X)
        Total cycles: 7 (always 7, regardless of page crossing)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.X) & 0xFFFF

        value = cpu.bus.read(addr)
        result = (value + 1) & 0xFF
        cpu.bus.write(addr, result)

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # RMW abs,X is always 7 cycles, no extra page-cross penalty
        cpu.cycles += 4

    def dec_abs(self, cpu):
        """
        DEC abs — Decrement Memory (Absolute)
        Total cycles: 6
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        addr = (hi << 8) | lo
        value = cpu.bus.read(addr)
        result = (value - 1) & 0xFF
        cpu.bus.write(addr, result)

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 3

    def dec_absx(self, cpu):
        """
        DEC abs,X — Decrement Memory (Absolute,X)
        Total cycles: 7 (always 7, regardless of page crossing)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.X) & 0xFFFF

        value = cpu.bus.read(addr)
        result = (value - 1) & 0xFF
        cpu.bus.write(addr, result)

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        # RMW abs,X is always 7 cycles, no extra page-cross penalty
        cpu.cycles += 4

    def sty_abs(self, cpu):
        """
        STY abs — Store Y Register (Absolute)
        Total cycles: 4
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        addr = (hi << 8) | lo
        cpu.bus.write(addr, cpu.Y)
        cpu.cycles += 1

    def stx_abs(self, cpu):
        """
        STX abs — Store X Register (Absolute)
        Total cycles: 4
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        addr = (hi << 8) | lo
        cpu.bus.write(addr, cpu.X)
        cpu.cycles += 1

    def stx_zpy(self, cpu):
        """
        STX zp,Y — Store X Register (Zero Page,Y)
        Total cycles: 4
        """
        base = cpu.fetch_byte()
        addr = (base + cpu.Y) & 0xFF
        cpu.bus.write(addr, cpu.X)
        cpu.cycles += 2

    def ldx_abs(self, cpu):
        """
        LDX abs — Load X Register (Absolute)
        Total cycles: 4
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        addr = (hi << 8) | lo
        value = cpu.bus.read(addr)
        cpu.X = value & 0xFF

        if cpu.X == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.X & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def ldx_absy(self, cpu):
        """
        LDX abs,Y — Load X Register (Absolute,Y)
        Total cycles: 4 (+1 if page crossed)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.Y) & 0xFFFF
        value = cpu.bus.read(addr)
        cpu.X = value & 0xFF

        if cpu.X == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.X & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 1

        if (base & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1

    def ldy_abs(self, cpu):
        """
        LDY abs — Load Y Register (Absolute)
        Total cycles: 4
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        addr = (hi << 8) | lo
        value = cpu.bus.read(addr)
        cpu.Y = value & 0xFF

        if cpu.Y == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.Y & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def ldy_absx(self, cpu):
        """
        LDY abs,X — Load Y Register (Absolute,X)
        Total cycles: 4 (+1 if page crossed)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.X) & 0xFFFF
        value = cpu.bus.read(addr)
        cpu.Y = value & 0xFF

        if cpu.Y == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.Y & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 1

        if (base & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1

    def eor_zpx(self, cpu):
        """
        EOR zp,X — Exclusive OR (Zero Page,X)
        Total cycles: 4
        """
        base = cpu.fetch_byte()
        addr = (base + cpu.X) & 0xFF
        value = cpu.bus.read(addr)
        cpu.A = (cpu.A ^ value) & 0xFF

        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 2

    def eor_absy(self, cpu):
        """
        EOR abs,Y — Exclusive OR (Absolute,Y)
        Total cycles: 4 (+1 if page crossed)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.Y) & 0xFFFF
        value = cpu.bus.read(addr)
        cpu.A = (cpu.A ^ value) & 0xFF

        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 1

        if (base & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1

    def ora_absy(self, cpu):
        """
        ORA abs,Y — Logical Inclusive OR (Absolute,Y)
        Total cycles: 4 (+1 if page crossed)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.Y) & 0xFFFF
        value = cpu.bus.read(addr)
        cpu.A = (cpu.A | value) & 0xFF

        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 1

        if (base & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1

    def ora_indy(self, cpu):
        """
        ORA (zp),Y — Logical Inclusive OR (Indirect Indexed)
        Total cycles: 5 (+1 if page crossed)
        """
        base = cpu.fetch_byte()
        lo = cpu.bus.read(base)
        hi = cpu.bus.read((base + 1) & 0xFF)
        base_addr = (hi << 8) | lo
        addr = (base_addr + cpu.Y) & 0xFFFF

        value = cpu.bus.read(addr)
        cpu.A = (cpu.A | value) & 0xFF

        if cpu.A == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if cpu.A & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 3

        if (base_addr & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1

    def cmp_zp(self, cpu):
        """
        CMP zp — Compare Accumulator (Zero Page)
        Total cycles: 3
        """
        addr = cpu.fetch_byte()
        value = cpu.bus.read(addr)
        result = (cpu.A - value) & 0xFF

        if cpu.A >= value:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def cmp_abs(self, cpu):
        """
        CMP abs — Compare Accumulator (Absolute)
        Total cycles: 4
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        addr = (hi << 8) | lo
        value = cpu.bus.read(addr)
        result = (cpu.A - value) & 0xFF

        if cpu.A >= value:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def cmp_absx(self, cpu):
        """
        CMP abs,X — Compare Accumulator (Absolute,X)
        Total cycles: 4 (+1 if page crossed)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.X) & 0xFFFF
        value = cpu.bus.read(addr)
        result = (cpu.A - value) & 0xFF

        if cpu.A >= value:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 1

        if (base & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1

    def cmp_indx(self, cpu):
        """
        CMP (zp,X) — Compare Accumulator (Indexed Indirect)
        Total cycles: 6
        """
        base = cpu.fetch_byte()
        zp = (base + cpu.X) & 0xFF
        lo = cpu.bus.read(zp)
        hi = cpu.bus.read((zp + 1) & 0xFF)
        addr = (hi << 8) | lo
        value = cpu.bus.read(addr)
        result = (cpu.A - value) & 0xFF

        if cpu.A >= value:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 4

    def cmp_indy(self, cpu):
        """
        CMP (zp),Y — Compare Accumulator (Indirect Indexed)
        Total cycles: 5 (+1 if page crossed)
        """
        base = cpu.fetch_byte()
        lo = cpu.bus.read(base)
        hi = cpu.bus.read((base + 1) & 0xFF)
        base_addr = (hi << 8) | lo
        addr = (base_addr + cpu.Y) & 0xFFFF
        value = cpu.bus.read(addr)
        result = (cpu.A - value) & 0xFF

        if cpu.A >= value:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        cpu.cycles += 3

        if (base_addr & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1

    def cpx_zp(self, cpu):
        """
        CPX zp — Compare X Register (Zero Page)
        Total cycles: 3
        """
        addr = cpu.fetch_byte()
        value = cpu.bus.read(addr)
        result = (cpu.X - value) & 0xFF

        if cpu.X >= value:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def cpx_abs(self, cpu):
        """
        CPX abs — Compare X Register (Absolute)
        Total cycles: 4
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        addr = (hi << 8) | lo
        value = cpu.bus.read(addr)
        result = (cpu.X - value) & 0xFF

        if cpu.X >= value:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def cpy_zp(self, cpu):
        """
        CPY zp — Compare Y Register (Zero Page)
        Total cycles: 3
        """
        addr = cpu.fetch_byte()
        value = cpu.bus.read(addr)
        result = (cpu.Y - value) & 0xFF

        if cpu.Y >= value:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def cpy_abs(self, cpu):
        """
        CPY abs — Compare Y Register (Absolute)
        Total cycles: 4
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        addr = (hi << 8) | lo
        value = cpu.bus.read(addr)
        result = (cpu.Y - value) & 0xFF

        if cpu.Y >= value:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80
        cpu.cycles += 1

    def sbc_abs(self, cpu):
        """
        SBC abs — Subtract with Carry (Absolute)
        Total cycles: 4
        Decimal mode ignored (6507 behavior)
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        addr = (hi << 8) | lo
        value = cpu.bus.read(addr)
        a = cpu.A
        c = 1 if (cpu.P & 0x01) else 0
        result = a - value - (1 - c)
        result8 = result & 0xFF
        cpu.A = result8

        if result >= 0:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result8 == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result8 & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        if ((a ^ result8) & (a ^ value) & 0x80) != 0:
            cpu.P |= 0x40
        else:
            cpu.P &= ~0x40

        cpu.cycles += 1

    def sbc_absy(self, cpu):
        """
        SBC abs,Y — Subtract with Carry (Absolute,Y)
        Total cycles: 4 (+1 if page crossed)
        Decimal mode ignored
        """
        lo = cpu.fetch_byte()
        hi = cpu.fetch_byte()
        base = (hi << 8) | lo
        addr = (base + cpu.Y) & 0xFFFF
        value = cpu.bus.read(addr)
        a = cpu.A
        c = 1 if (cpu.P & 0x01) else 0
        result = a - value - (1 - c)
        result8 = result & 0xFF
        cpu.A = result8

        if result >= 0:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result8 == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result8 & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        if ((a ^ result8) & (a ^ value) & 0x80) != 0:
            cpu.P |= 0x40
        else:
            cpu.P &= ~0x40

        cpu.cycles += 1

        if (base & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1

    def sbc_indx(self, cpu):
        """
        SBC (zp,X) — Subtract with Carry (Indexed Indirect)
        Total cycles: 6
        Decimal mode ignored
        """
        base = cpu.fetch_byte()
        zp = (base + cpu.X) & 0xFF
        lo = cpu.bus.read(zp)
        hi = cpu.bus.read((zp + 1) & 0xFF)
        addr = (hi << 8) | lo
        value = cpu.bus.read(addr)
        a = cpu.A
        c = 1 if (cpu.P & 0x01) else 0
        result = a - value - (1 - c)
        result8 = result & 0xFF
        cpu.A = result8

        if result >= 0:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result8 == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result8 & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        if ((a ^ result8) & (a ^ value) & 0x80) != 0:
            cpu.P |= 0x40
        else:
            cpu.P &= ~0x40
        cpu.cycles += 4

    def sbc_indy(self, cpu):
        """
        SBC (zp),Y — Subtract with Carry (Indirect Indexed)
        Total cycles: 5 (+1 if page crossed)
        Decimal mode ignored
        """
        base = cpu.fetch_byte()
        lo = cpu.bus.read(base)
        hi = cpu.bus.read((base + 1) & 0xFF)
        base_addr = (hi << 8) | lo
        addr = (base_addr + cpu.Y) & 0xFFFF
        value = cpu.bus.read(addr)
        a = cpu.A
        c = 1 if (cpu.P & 0x01) else 0
        result = a - value - (1 - c)
        result8 = result & 0xFF
        cpu.A = result8

        if result >= 0:
            cpu.P |= 0x01
        else:
            cpu.P &= ~0x01

        if result8 == 0:
            cpu.P |= 0x02
        else:
            cpu.P &= ~0x02

        if result8 & 0x80:
            cpu.P |= 0x80
        else:
            cpu.P &= ~0x80

        if ((a ^ result8) & (a ^ value) & 0x80) != 0:
            cpu.P |= 0x40
        else:
            cpu.P &= ~0x40

        cpu.cycles += 3

        if (base_addr & 0xFF00) != (addr & 0xFF00):
            cpu.cycles += 1
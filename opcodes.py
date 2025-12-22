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
        Total cycles: 2 (+1 if branch taken)
        """
        offset = cpu.fetch_byte()   # operand fetch (1 cycle)

        # Check Negative flag (N = bit 7)
        if (cpu.P & 0x80) == 0:
            # Sign-extend offset
            if offset & 0x80:
                offset -= 0x100

            cpu.PC = (cpu.PC + offset) & 0xFFFF
            cpu.cycles += 1   # branch taken penalty
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
        # RTS pulls return address, then adds 1

        # pull low byte
        cpu.SP = (cpu.SP + 1) & 0xFF
        lo = cpu.bus.read(0x0100 + cpu.SP)

        # pull high byte
        cpu.SP = (cpu.SP + 1) & 0xFF
        hi = cpu.bus.read(0x0100 + cpu.SP)

        cpu.PC = ((hi << 8) | lo) + 1
        cpu.PC &= 0xFFFF

        cpu.cycles += 5  # opcode fetch already counted

    def brk(self, cpu):
        return_pc = (cpu.PC + 1) & 0xFFFF

        cpu.bus.write(0x0100 + cpu.SP, (return_pc >> 8) & 0xFF)
        cpu.SP = (cpu.SP - 1) & 0xFF

        cpu.bus.write(0x0100 + cpu.SP, return_pc & 0xFF)
        cpu.SP = (cpu.SP - 1) & 0xFF

        cpu.bus.write(0x0100 + cpu.SP, cpu.P | 0x10)
        cpu.SP = (cpu.SP - 1) & 0xFF

        cpu.P |= 0x04
        cpu.cycles += 6
        cpu.halted = True

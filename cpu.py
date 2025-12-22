# MOS Technology 6507
from opcodes import Opcodes
class CPU6507:
    def __init__(self, bus):
        self.bus = bus
        self.halted = False

        # Registers
        self.A = 0x00
        self.X = 0x00
        self.Y = 0x00
        self.SP = 0xFF
        self.P  = 0x24          # IRQ disabled, unused bit set
        self.PC = 0x0000        # FULL 16-bit PC

        self.cycles = 0
        self.ops = Opcodes()

        self.opcode_table = {
            0xEA: self.ops.nop,        # NOP
            0xA9: self.ops.lda_imm,    # LDA #imm
            0x4C: self.ops.jmp_abs,    # JMP abs
            0x0D: self.ops.ora_abs,    # ORA abs
            0xD0: self.ops.bne,        # BNE
            0xE8: self.ops.inx,        # INX
            0xCA: self.ops.dex,        # DEX
            0xD8: self.ops.cld,        # CLD
            0x78: self.ops.sei,        # SEI
            0xA2: self.ops.ldx_imm,    # LDX #imm
            0x9A: self.ops.txs,        # TXS
            0x8A: self.ops.txa,        # TXA
            0x95: self.ops.sta_zpx,    # STA zp,X
            0x85: self.ops.sta_zp,     # STA zp
            0x0A: self.ops.asl_a,      # ASL A
            0x86: self.ops.stx_zp,     # STX zp
            0x20: self.ops.jsr_abs,    # JSR abs
            0xA5: self.ops.lda_zp,     # LDA zp
            0x38: self.ops.sec,        # SEC
            0xE9: self.ops.sbc_imm,    # SBC #imm
            0x10: self.ops.bpl,        # BPL
            0x29: self.ops.and_imm,    # AND #imm
            0x18: self.ops.clc,        # CLC
            0x69: self.ops.adc_imm,    # ADC #imm
            0x09: self.ops.ora_imm,    # ORA #imm
            0xA0: self.ops.ldy_imm,    # LDY #imm
            0x94: self.ops.sty_zpx,    # STY zp,X
            0x60: self.ops.rts,        # RTS
            0x00: self.ops.brk,        # BRK
        }

    def reset(self):
        """
        Atari 2600 reset behavior.
        PC is forced by cartridge wiring, not vectors.
        """
        self.PC = 0xF000          # full 16-bit value
        self.SP = 0xFF
        self.P  = 0x24
        self.cycles = 0
        self.halted = False

    def fetch_byte(self) -> int:
        """
        Fetch one byte at PC.
        PC is NOT masked here.
        Bus handles address masking.
        """
        value = self.bus.read(self.PC)
        self.PC = (self.PC + 1) & 0xFFFF
        self.cycles += 1
        return value

    def step(self):
        """
        Execute one instruction.
        """
        if self.halted:
            return

        opcode_pc = self.PC
        opcode = self.fetch_byte()

        handler = self.opcode_table.get(opcode)
        if handler is None:
            raise RuntimeError(
                f"Unknown opcode {opcode:02X} at PC={opcode_pc:04X}"
            )

        handler(self)

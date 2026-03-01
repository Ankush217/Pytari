# MOS Technology 6507
# cpu.py
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
            # NOP
            0xEA: self.ops.nop,          # NOP

            # LDA
            0xA9: self.ops.lda_imm,      # LDA #imm
            0xA5: self.ops.lda_zp,       # LDA zp
            0xB5: self.ops.lda_zpx,      # LDA zp,X
            0xAD: self.ops.lda_abs,      # LDA abs
            0xBD: self.ops.lda_absx,     # LDA abs,X
            0xB9: self.ops.lda_absy,     # LDA abs,Y
            0xA1: self.ops.lda_indx,     # LDA (zp,X)
            0xB1: self.ops.lda_indy,     # LDA (zp),Y

            # LDX
            0xA2: self.ops.ldx_imm,      # LDX #imm
            0xA6: self.ops.ldx_zp,       # LDX zp
            0xB6: self.ops.ldx_zpy,      # LDX zp,Y
            0xAE: self.ops.ldx_abs,      # LDX abs
            0xBE: self.ops.ldx_absy,     # LDX abs,Y

            # LDY
            0xA0: self.ops.ldy_imm,      # LDY #imm
            0xA4: self.ops.ldy_zp,       # LDY zp
            0xB4: self.ops.ldy_zpx,      # LDY zp,X
            0xAC: self.ops.ldy_abs,      # LDY abs
            0xBC: self.ops.ldy_absx,     # LDY abs,X

            # STA
            0x85: self.ops.sta_zp,       # STA zp
            0x95: self.ops.sta_zpx,      # STA zp,X
            0x8D: self.ops.sta_abs,      # STA abs
            0x9D: self.ops.sta_absx,     # STA abs,X
            0x99: self.ops.sta_absy,     # STA abs,Y
            0x81: self.ops.sta_indx,     # STA (zp,X)
            0x91: self.ops.sta_indy,     # STA (zp),Y

            # STX
            0x86: self.ops.stx_zp,       # STX zp
            0x96: self.ops.stx_zpy,      # STX zp,Y
            0x8E: self.ops.stx_abs,      # STX abs

            # STY
            0x84: self.ops.sty_zp,       # STY zp
            0x94: self.ops.sty_zpx,      # STY zp,X
            0x8C: self.ops.sty_abs,      # STY abs

            # Transfer
            0xAA: self.ops.tax,          # TAX
            0xA8: self.ops.tay,          # TAY
            0x8A: self.ops.txa,          # TXA
            0x98: self.ops.tya,          # TYA
            0x9A: self.ops.txs,          # TXS
            0xBA: self.ops.tsx,          # TSX

            # Stack
            0x48: self.ops.pha,          # PHA
            0x68: self.ops.pla,          # PLA
            0x08: self.ops.php,          # PHP
            0x28: self.ops.plp,          # PLP

            # ADC
            0x69: self.ops.adc_imm,      # ADC #imm
            0x65: self.ops.adc_zp,       # ADC zp
            0x75: self.ops.adc_zpx,      # ADC zp,X
            0x6D: self.ops.adc_abs,      # ADC abs
            0x7D: self.ops.adc_absx,     # ADC abs,X
            0x79: self.ops.adc_absy,     # ADC abs,Y
            0x61: self.ops.adc_indx,     # ADC (zp,X)
            0x71: self.ops.adc_indy,     # ADC (zp),Y

            # SBC
            0xE9: self.ops.sbc_imm,      # SBC #imm
            0xE5: self.ops.sbc_zp,       # SBC zp
            0xF5: self.ops.sbc_zpx,      # SBC zp,X  ← was missing
            0xED: self.ops.sbc_abs,      # SBC abs
            0xFD: self.ops.sbc_absx,     # SBC abs,X
            0xF9: self.ops.sbc_absy,     # SBC abs,Y
            0xE1: self.ops.sbc_indx,     # SBC (zp,X)
            0xF1: self.ops.sbc_indy,     # SBC (zp),Y

            # AND
            0x29: self.ops.and_imm,      # AND #imm
            0x25: self.ops.and_zp,       # AND zp
            0x35: self.ops.and_zpx,      # AND zp,X
            0x2D: self.ops.and_abs,      # AND abs
            0x3D: self.ops.and_absx,     # AND abs,X
            0x39: self.ops.and_absy,     # AND abs,Y
            0x21: self.ops.and_indx,     # AND (zp,X)
            0x31: self.ops.and_indy,     # AND (zp),Y

            # ORA
            0x09: self.ops.ora_imm,      # ORA #imm
            0x05: self.ops.ora_zp,       # ORA zp
            0x15: self.ops.ora_zpx,      # ORA zp,X
            0x0D: self.ops.ora_abs,      # ORA abs
            0x1D: self.ops.ora_absx,     # ORA abs,X
            0x19: self.ops.ora_absy,     # ORA abs,Y
            0x01: self.ops.ora_indx,     # ORA (zp,X)
            0x11: self.ops.ora_indy,     # ORA (zp),Y

            # EOR
            0x49: self.ops.eor_imm,      # EOR #imm
            0x45: self.ops.eor_zp,       # EOR zp
            0x55: self.ops.eor_zpx,      # EOR zp,X
            0x4D: self.ops.eor_abs,      # EOR abs
            0x5D: self.ops.eor_absx,     # EOR abs,X
            0x59: self.ops.eor_absy,     # EOR abs,Y
            0x41: self.ops.eor_indx,     # EOR (zp,X)
            0x51: self.ops.eor_indy,     # EOR (zp),Y

            # CMP
            0xC9: self.ops.cmp_imm,      # CMP #imm
            0xC5: self.ops.cmp_zp,       # CMP zp
            0xD5: self.ops.cmp_zpx,      # CMP zp,X  ← was missing
            0xCD: self.ops.cmp_abs,      # CMP abs
            0xDD: self.ops.cmp_absx,     # CMP abs,X
            0xD9: self.ops.cmp_absy,     # CMP abs,Y  ← was missing
            0xC1: self.ops.cmp_indx,     # CMP (zp,X)
            0xD1: self.ops.cmp_indy,     # CMP (zp),Y

            # CPX
            0xE0: self.ops.cpx_imm,      # CPX #imm
            0xE4: self.ops.cpx_zp,       # CPX zp
            0xEC: self.ops.cpx_abs,      # CPX abs

            # CPY
            0xC0: self.ops.cpy_imm,      # CPY #imm
            0xC4: self.ops.cpy_zp,       # CPY zp
            0xCC: self.ops.cpy_abs,      # CPY abs

            # ASL
            0x0A: self.ops.asl_a,        # ASL A
            0x06: self.ops.asl_zp,       # ASL zp   ← was missing
            0x16: self.ops.asl_zpx,      # ASL zp,X ← was missing
            0x0E: self.ops.asl_abs,      # ASL abs  ← was missing
            0x1E: self.ops.asl_absx,     # ASL abs,X ← was missing

            # LSR
            0x4A: self.ops.lsr_a,        # LSR A
            0x46: self.ops.lsr_zp,       # LSR zp
            0x56: self.ops.lsr_zpx,      # LSR zp,X
            0x4E: self.ops.lsr_abs,      # LSR abs
            0x5E: self.ops.lsr_absx,     # LSR abs,X

            # ROL
            0x2A: self.ops.rol_a,        # ROL A
            0x26: self.ops.rol_zp,       # ROL zp
            0x36: self.ops.rol_zpx,      # ROL zp,X
            0x2E: self.ops.rol_abs,      # ROL abs
            0x3E: self.ops.rol_absx,     # ROL abs,X

            # ROR
            0x6A: self.ops.ror_a,        # ROR A
            0x66: self.ops.ror_zp,       # ROR zp
            0x76: self.ops.ror_zpx,      # ROR zp,X
            0x6E: self.ops.ror_abs,      # ROR abs
            0x7E: self.ops.ror_absx,     # ROR abs,X

            # INC
            0xE6: self.ops.inc_zp,       # INC zp
            0xF6: self.ops.inc_zpx,      # INC zp,X
            0xEE: self.ops.inc_abs,      # INC abs
            0xFE: self.ops.inc_absx,     # INC abs,X

            # DEC
            0xC6: self.ops.dec_zp,       # DEC zp
            0xD6: self.ops.dec_zpx,      # DEC zp,X  ← was missing
            0xCE: self.ops.dec_abs,      # DEC abs
            0xDE: self.ops.dec_absx,     # DEC abs,X

            # INX / INY / DEX / DEY
            0xE8: self.ops.inx,          # INX
            0xC8: self.ops.iny,          # INY
            0xCA: self.ops.dex,          # DEX
            0x88: self.ops.dey,          # DEY

            # BIT
            0x24: self.ops.bit_zp,       # BIT zp
            0x2C: self.ops.bit_abs,      # BIT abs

            # Branches
            0x10: self.ops.bpl,          # BPL
            0x30: self.ops.bmi,          # BMI
            0x50: self.ops.bvc,          # BVC
            0x70: self.ops.bvs,          # BVS
            0x90: self.ops.bcc,          # BCC
            0xB0: self.ops.bcs,          # BCS
            0xD0: self.ops.bne,          # BNE
            0xF0: self.ops.beq,          # BEQ

            # Jumps / Subroutine
            0x4C: self.ops.jmp_abs,      # JMP abs
            0x6C: self.ops.jmp_ind,      # JMP (ind)  ← was missing
            0x20: self.ops.jsr_abs,      # JSR abs
            0x60: self.ops.rts,          # RTS
            0x40: self.ops.rti,          # RTI  ← was missing

            # Flags
            0x18: self.ops.clc,          # CLC
            0x38: self.ops.sec,          # SEC
            0x78: self.ops.sei,          # SEI
            0xB8: self.ops.clv,          # CLV
            0xD8: self.ops.cld,          # CLD
            0xF8: self.ops.sed,          # SED

            # Misc
            0x00: self.ops.brk,          # BRK

            # Illegal opcodes
            0xFC: self.ops.ill_nop_absx, # NOP abs,X (illegal)
            0xFF: self.ops.ill_isc_absx, # ISC abs,X (illegal)
            0xC7: self.ops.ill_dcp_zp,   # DCP zp    (illegal)
            0x62: self.ops.ill_kil,      # KIL / JAM (illegal)
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

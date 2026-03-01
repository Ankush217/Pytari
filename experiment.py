from cpu import CPU6507
from bus import Atari2600Bus, RIOT, Cartridge
from pathlib import Path
from tia import TIA

ROM_PATH = Path("PM.a26")
LOG_PATH = Path("Output.log")
cyc = 100000


def load_rom(path: Path) -> bytes:
    if not path.exists():
        raise FileNotFoundError(f"ROM not found: {path}")
    data = path.read_bytes()
    if len(data) != 4096:
        raise ValueError(f"Expected 4KB ROM, got {len(data)} bytes")
    return data


def main():
    # Clear log
    with open(LOG_PATH, "w") as log:
        log.write("")

    def log_print(*args):
        with open(LOG_PATH, "a") as log:
            log.write(" ".join(str(a) for a in args) + "\n")

    rom = load_rom(ROM_PATH)

    cart = Cartridge(rom)
    tia = TIA()
    riot = RIOT()
    bus = Atari2600Bus(cart, tia, riot)
    cpu = CPU6507(bus)

    # --- Optional: stack tracing ---
    original_write = bus.write
    def traced_write(address, value):
        if 0x0100 <= (address & 0x1FFF) <= 0x01FF:
            log_print(f"  *** STACK WRITE: addr=0x{address:04X} value=0x{value:02X} SP=0x{cpu.SP:02X}")
        original_write(address, value)
    bus.write = traced_write

    original_read = bus.read
    def traced_read(address):
        value = original_read(address)
        if 0x0100 <= (address & 0x1FFF) <= 0x01FF:
            log_print(f"  *** STACK READ:  addr=0x{address:04X} value=0x{value:02X} SP=0x{cpu.SP:02X}")
        return value
    bus.read = traced_read

    cpu.reset()

    log_print("=== A26 + TIA DEBUG EXPERIMENT ===")
    log_print(f"ROM: {ROM_PATH}")
    log_print(f"Reset PC: {cpu.PC:04X}")
    log_print("")

    for step in range(cyc):

        if cpu.halted:
            log_print("CPU HALTED (BRK)")
            break

        pc_before = cpu.PC
        opcode = original_read(cpu.PC)

        cpu.step()   # This now advances TIA automatically

        # Log instruction
        log_print(f"[{step}] PC={pc_before:04X} OPCODE={opcode:02X}")
        log_print(
            f"    A={cpu.A:02X} "
            f"X={cpu.X:02X} "
            f"Y={cpu.Y:02X} "
            f"P={cpu.P:08b} "
            f"SP={cpu.SP:02X} "
            f"PC={cpu.PC:04X} "
            f"CYC={cpu.cycles}"
        )

        # --- TIA state snapshot ---
        log_print(
            f"    TIA: frame={tia.frame} "
            f"scanline={tia.scanline} "
            f"color_clock={tia.color_clock} "
            f"VSYNC={int(tia.vsync)} "
            f"VBLANK={int(tia.vblank)}"
        )

        # --- Frame boundary detection ---
        if tia.frame_ready:
            log_print(f"\n=== FRAME {tia.frame} COMPLETE ===\n")
            tia.consume_frame()

        log_print("")


if __name__ == "__main__":
    main()
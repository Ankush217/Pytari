from cpu import CPU6507
from bus import Atari2600Bus, TIA, RIOT, Cartridge
from pathlib import Path


ROM_PATH = Path("PM.a26")
MAX_STEPS = 10_000_000


def load_rom(path: Path) -> bytes:
    if not path.exists():
        raise FileNotFoundError(f"ROM not found: {path}")
    data = path.read_bytes()
    if len(data) != 4096:
        raise ValueError(f"Expected 4KB ROM, got {len(data)} bytes")
    return data


def main():
    rom = load_rom(ROM_PATH)

    cart = Cartridge(rom)
    tia = TIA()
    riot = RIOT()
    bus = Atari2600Bus(cart, tia, riot)
    cpu = CPU6507(bus)

    cpu.reset()

    step = 0

    try:
        while step < MAX_STEPS:
            if cpu.halted:
                break

            pc_before = cpu.PC
            opcode = bus.read(cpu.PC)

            cpu.step()
            step += 1

    except Exception:
        print("{CPU CRASH}")
        print(f"[{step}] PC={pc_before:04X} OPCODE={opcode:02X}")
        print(
            f"    A={cpu.A:02X} "
            f"X={cpu.X:02X} "
            f"Y={cpu.Y:02X} "
            f"P={cpu.P:08b} "
            f"SP={cpu.SP:02X} "
            f"PC={cpu.PC:04X} "
            f"CYC={cpu.cycles}"
        )
        return
    print(f"Completed {step} instructions without crash.")
if __name__ == "__main__":
    main()
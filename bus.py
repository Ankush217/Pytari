class Bus:
    def read(self, address: int) -> int:
        raise NotImplementedError

    def write(self, address: int, value: int) -> None:
        raise NotImplementedError


class Atari2600Bus(Bus):
    def __init__(self, cartridge, tia, riot):
        self.cartridge = cartridge
        self.tia = tia
        self.riot = riot
        self.last_value = 0x00  # open bus

    def read(self, address: int) -> int:
        address &= 0x1FFF  # 13-bit address bus

        # --- ROM: A12 = 1 ---
        if address & 0x1000:
            value = self.cartridge.read(address & 0x0FFF)
            if value is not None:
                self.last_value = value & 0xFF
            return self.last_value

        # --- RIOT: A7 = 1 (STACK LIVES HERE) ---
        if address & 0x0080:
            value = self.riot.read(address & 0x007F)
            if value is not None:
                self.last_value = value & 0xFF
            return self.last_value

        # --- TIA: A12 = 0, A7 = 0 ---
        value = self.tia.read(address & 0x003F)
        if value is not None:
            self.last_value = value & 0xFF
        return self.last_value

    def write(self, address: int, value: int) -> None:
        address &= 0x1FFF
        value &= 0xFF

        # data appears on bus even if device ignores it
        self.last_value = value

        # --- ROM ---
        if address & 0x1000:
            self.cartridge.write(address & 0x0FFF, value)
            return

        # --- RIOT (STACK!) ---
        if address & 0x0080:
            self.riot.write(address & 0x007F, value)
            return

        # --- TIA ---
        self.tia.write(address & 0x003F, value)


class TIA:
    def read(self, address: int) -> int:
        return None  # unmapped → open bus

    def write(self, address: int, value: int) -> None:
        pass


class RIOT:
    def __init__(self):
        self.ram = bytearray(128)
        self.io = bytearray(32)

    def read(self, address: int) -> int:
        address &= 0x7F

        # RAM: A5 = 0
        if (address & 0x20) == 0:
            return self.ram[address & 0x1F]

        # I/O: A6 = 0
        if (address & 0x40) == 0:
            return self.io[address & 0x1F]

        return None

    def write(self, address: int, value: int) -> None:
        address &= 0x7F

        if (address & 0x20) == 0:
            self.ram[address & 0x1F] = value
            return

        if (address & 0x40) == 0:
            self.io[address & 0x1F] = value
            return


class Cartridge:
    def __init__(self, rom: bytes):
        self.rom = rom

    def read(self, address: int) -> int:
        return self.rom[address % len(self.rom)]

    def write(self, address: int, value: int) -> None:
        pass

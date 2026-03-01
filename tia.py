# tia.py
# TIA (Television Interface Adaptor) — Atari 2600 / MOS 6507
#
# Verified register map (Stella Programmer's Guide, Table 1):
#
#  WRITE:
#   0x00 VSYNC   0x01 VBLANK  0x02 WSYNC   0x03 RSYNC
#   0x04 NUSIZ0  0x05 NUSIZ1  0x06 COLUP0  0x07 COLUP1
#   0x08 COLUPF  0x09 COLUBK  0x0A CTRLPF  0x0B REFP0
#   0x0C REFP1   0x0D PF0     0x0E PF1     0x0F PF2
#   0x10 RESP0   0x11 RESP1   0x12 RESM0   0x13 RESM1
#   0x14 RESBL   0x15 AUDC0   0x16 AUDC1   0x17 AUDF0
#   0x18 AUDF1   0x19 AUDV0   0x1A AUDV1   0x1B GRP0
#   0x1C GRP1    0x1D ENAM0   0x1E ENAM1   0x1F ENABL
#   0x20 HMP0    0x21 HMP1    0x22 HMM0    0x23 HMM1
#   0x24 HMBL    0x25 VDELP0  0x26 VDELP1  0x27 VDELBL
#   0x28 RESMP0  0x29 RESMP1  0x2A HMOVE   0x2B HMCLR
#   0x2C CXCLR
#
#  READ:
#   0x00 CXM0P   0x01 CXM1P   0x02 CXP0FB  0x03 CXP1FB
#   0x04 CXM0FB  0x05 CXM1FB  0x06 CXBLPF  0x07 CXPPMM
#   0x08 INPT0   0x09 INPT1   0x0A INPT2   0x0B INPT3
#   0x0C INPT4   0x0D INPT5

# ── NTSC colour palette ───────────────────────────────────────────────────────
# 128 entries; index = (color_register & 0xFE) >> 1
_NTSC_RGB = [
    # 0x00-0x0E  Greys
    (0,0,0),(68,68,68),(116,116,116),(158,158,158),
    (196,196,196),(228,228,228),(255,255,255),(255,255,255),
    # 0x10-0x1E  Gold/Orange
    (68,0,0),(116,12,0),(160,36,0),(200,68,0),
    (228,100,0),(248,136,0),(252,172,0),(252,208,0),
    # 0x20-0x2E  Orange-Yellow
    (68,16,0),(116,40,0),(160,72,0),(200,108,0),
    (236,148,0),(248,184,0),(252,216,0),(252,244,0),
    # 0x30-0x3E  Yellow
    (52,24,0),(92,52,0),(136,88,0),(180,124,4),
    (220,164,28),(244,196,60),(252,228,92),(252,252,124),
    # 0x40-0x4E  Lime
    (16,36,0),(40,68,0),(72,104,0),(112,140,0),
    (152,176,0),(188,212,0),(216,240,0),(244,252,0),
    # 0x50-0x5E  Green-Yellow
    (0,44,0),(0,76,4),(0,116,20),(24,152,52),
    (56,188,84),(88,220,120),(120,248,152),(156,252,180),
    # 0x60-0x6E  Green
    (0,40,16),(0,72,40),(0,108,72),(0,148,108),
    (0,184,148),(0,216,188),(0,248,224),(0,252,252),
    # 0x70-0x7E  Cyan-Green
    (0,32,48),(0,64,88),(0,100,132),(0,136,176),
    (0,168,220),(0,200,252),(0,228,252),(0,252,252),
    # 0x80-0x8E  Cyan-Blue
    (0,20,68),(0,52,112),(0,88,160),(0,124,204),
    (0,160,244),(0,192,252),(0,224,252),(0,252,252),
    # 0x90-0x9E  Sky Blue
    (16,0,92),(36,20,136),(64,52,180),(96,88,220),
    (128,124,252),(160,160,252),(192,196,252),(220,228,252),
    # 0xA0-0xAE  Blue
    (48,0,100),(80,12,148),(116,44,192),(148,80,228),
    (180,116,252),(208,152,252),(232,184,252),(252,212,252),
    # 0xB0-0xBE  Violet
    (68,0,68),(108,0,116),(148,16,164),(188,52,200),
    (220,92,232),(248,128,252),(252,164,252),(252,196,252),
    # 0xC0-0xCE  Purple
    (68,0,28),(116,0,60),(164,8,92),(204,44,128),
    (236,84,160),(252,124,188),(252,160,212),(252,192,232),
    # 0xD0-0xDE  Pink/Red
    (64,0,0),(108,0,0),(152,0,0),(196,0,0),
    (232,0,0),(252,40,0),(252,80,0),(252,120,0),
]
while len(_NTSC_RGB) < 128:
    _NTSC_RGB.append((0, 0, 0))
_NTSC_RGB = _NTSC_RGB[:128]

_PALETTE_RGBA = bytearray(128 * 4)
for _i, (_r, _g, _b) in enumerate(_NTSC_RGB):
    _PALETTE_RGBA[_i*4:_i*4+4] = bytes([_r, _g, _b, 255])

def _color_rgb(color_reg: int):
    """Return (r, g, b) for a TIA colour register value (bit 0 ignored)."""
    idx  = (color_reg & 0xFE) >> 1
    base = idx * 4
    return _PALETTE_RGBA[base], _PALETTE_RGBA[base+1], _PALETTE_RGBA[base+2]


# ── NUSIZ tables ──────────────────────────────────────────────────────────────
# bits 2-0 of NUSIZ → list of pixel offsets from resp where copies start
_NUSIZ_OFFSETS = {
    0: [0],           # one copy
    1: [0, 16],       # two copies, close
    2: [0, 32],       # two copies, medium
    3: [0, 16, 32],   # three copies, close
    4: [0, 64],       # two copies, wide
    5: [0],           # one copy, double-width
    6: [0, 32, 64],   # three copies, medium
    7: [0],           # one copy, quad-width
}
_NUSIZ_STRETCH = {0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 2, 6: 1, 7: 4}

# 2-bit size field → pixel width  (used by missiles and ball)
_SIZE_WIDTH = {0: 1, 1: 2, 2: 4, 3: 8}


class TIA:
    """
    Cycle-accurate NTSC TIA emulation for the Atari 2600.

    Tick model
    ----------
    tick() advances one TIA color clock.  cpu.step() calls it 3× per CPU
    cycle automatically (already wired in cpu.py).

    WSYNC
    -----
    Writing WSYNC sets wsync_pending = True.  tick() continues advancing
    the beam (suppressing pixel output) until color_clock reaches 0 on the
    next scanline, at which point wsync_pending clears automatically.
    The main loop must NOT call cpu.step() while wsync_pending is True;
    instead call tia.tick() directly until it clears.

    Framebuffer
    -----------
    self.framebuffer  flat bytearray, RGBA32, 160 × 192 pixels, row-major.
    self.frame_ready  True when a complete frame is available.
    consume_frame()   clears frame_ready, returns a copy of the buffer.
    """

    COLOR_CLOCKS_PER_SCANLINE = 228
    HBLANK_CLOCKS             = 68      # clocks 0-67 are hblank
    VISIBLE_PIXELS            = 160     # clocks 68-227 are active video
    TOTAL_SCANLINES           = 262
    VISIBLE_START_LINE        = 40      # skip VSYNC (3) + VBLANK (37) lines
    VISIBLE_SCANLINES         = 192

    def __init__(self):
        # ── Beam ─────────────────────────────────────────────────────────────
        self.color_clock = 0
        self.scanline    = 0
        self.frame       = 0

        # ── Sync ─────────────────────────────────────────────────────────────
        self.vsync         = False
        self._prev_vsync   = False
        self.vblank        = False      # set by VBLANK bit 7
        self.wsync_pending = False

        # ── HMOVE blank counter ───────────────────────────────────────────────
        # After HMOVE the leftmost 8 active pixels are forced black.
        self._hmove_blank_ctr = 0

        # ── Playfield ────────────────────────────────────────────────────────
        self.pf0    = 0   # only bits 7-4 used; bit4=leftmost PF pixel
        self.pf1    = 0   # bit7=leftmost
        self.pf2    = 0   # bit0=leftmost
        self.ctrlpf = 0   # bit0=reflect, bit1=score, bit2=priority, bits5-4=ball size
        self.colupf = 0
        self.colubk = 0

        # ── Player 0 ─────────────────────────────────────────────────────────
        self.colup0 = 0
        self.nusiz0 = 0   # bits2-0=copy mode, bits5-4=missile width
        self.refp0  = False
        self.grp0   = 0   # active graphic
        self._grp0d = 0   # delayed graphic (VDELP0)
        self.vdelp0 = False
        self.resp0  = 0   # horizontal pixel position (0-159)
        self.hmp0   = 0   # raw upper nibble of HMP0 register

        # ── Player 1 ─────────────────────────────────────────────────────────
        self.colup1 = 0
        self.nusiz1 = 0
        self.refp1  = False
        self.grp1   = 0
        self._grp1d = 0
        self.vdelp1 = False
        self.resp1  = 0
        self.hmp1   = 0

        # ── Missile 0 ────────────────────────────────────────────────────────
        self.enam0  = False
        self.resm0  = 0
        self.hmm0   = 0
        self.resmp0 = False   # lock missile to player

        # ── Missile 1 ────────────────────────────────────────────────────────
        self.enam1  = False
        self.resm1  = 0
        self.hmm1   = 0
        self.resmp1 = False

        # ── Ball ─────────────────────────────────────────────────────────────
        self.enabl   = False
        self._enabld = False  # delayed ENABL (written via GRP1)
        self.vdelbl  = False
        self.resbl   = 0
        self.hmbl    = 0

        # ── Audio ─────────────────────────────────────────────────────────────
        self.audc = [0, 0]
        self.audf = [0, 0]
        self.audv = [0, 0]

        # ── Collision latches ─────────────────────────────────────────────────
        self._cx = {
            'M0P1': False, 'M0P0': False,   # CXM0P  read 0x00
            'M1P1': False, 'M1P0': False,   # CXM1P  read 0x01
            'P0PF': False, 'P0BL': False,   # CXP0FB read 0x02
            'P1PF': False, 'P1BL': False,   # CXP1FB read 0x03
            'M0PF': False, 'M0BL': False,   # CXM0FB read 0x04
            'M1PF': False, 'M1BL': False,   # CXM1FB read 0x05
            'BLPF': False,                  # CXBLPF read 0x06
            'P0P1': False, 'M0M1': False,   # CXPPMM read 0x07
        }

        # ── Framebuffer ───────────────────────────────────────────────────────
        self.framebuffer = bytearray(self.VISIBLE_PIXELS * self.VISIBLE_SCANLINES * 4)
        self.frame_ready = False

    # =========================================================================
    # Bus interface — READ
    # =========================================================================

    def read(self, address: int):
        """
        TIA read-side.  Only bits 7-6 are driven; bits 5-0 float (open bus).
        The bus layer supplies the open-bus value for the lower bits.
        """
        address &= 0x0F          # A4 and higher are don't-care on reads
        cx = self._cx

        if address == 0x00: return (cx['M0P1'] << 7) | (cx['M0P0'] << 6)
        if address == 0x01: return (cx['M1P1'] << 7) | (cx['M1P0'] << 6)
        if address == 0x02: return (cx['P0PF'] << 7) | (cx['P0BL'] << 6)
        if address == 0x03: return (cx['P1PF'] << 7) | (cx['P1BL'] << 6)
        if address == 0x04: return (cx['M0PF'] << 7) | (cx['M0BL'] << 6)
        if address == 0x05: return (cx['M1PF'] << 7) | (cx['M1BL'] << 6)
        if address == 0x06: return (cx['BLPF'] << 7)
        if address == 0x07: return (cx['P0P1'] << 7) | (cx['M0M1'] << 6)
        if address in (0x08, 0x09, 0x0A, 0x0B): return 0x00   # paddle (not impl)
        if address in (0x0C, 0x0D): return 0x80               # fire btn not pressed

        return None   # open bus

    # =========================================================================
    # Bus interface — WRITE
    # =========================================================================

    def write(self, address: int, value: int):
        address &= 0x3F
        value   &= 0xFF

        # ── 0x00  VSYNC ───────────────────────────────────────────────────────
        if address == 0x00:
            new_vsync = bool(value & 0x02)
            if self._prev_vsync and not new_vsync:
                self._end_frame()
            self.vsync       = new_vsync
            self._prev_vsync = new_vsync

        # ── 0x01  VBLANK  (bit 7 blanks video, NOT bit 1) ────────────────────
        elif address == 0x01:
            self.vblank = bool(value & 0x80)

        # ── 0x02  WSYNC ───────────────────────────────────────────────────────
        elif address == 0x02:
            self.wsync_pending = True

        # ── 0x03  RSYNC ───────────────────────────────────────────────────────
        elif address == 0x03:
            self.color_clock = 0    # snap beam (rare, e.g. some games reset timing)

        # ── 0x04-0x05  NUSIZ ─────────────────────────────────────────────────
        elif address == 0x04: self.nusiz0 = value
        elif address == 0x05: self.nusiz1 = value

        # ── 0x06-0x09  Colours ───────────────────────────────────────────────
        elif address == 0x06: self.colup0 = value & 0xFE
        elif address == 0x07: self.colup1 = value & 0xFE
        elif address == 0x08: self.colupf = value & 0xFE
        elif address == 0x09: self.colubk = value & 0xFE

        # ── 0x0A  CTRLPF ─────────────────────────────────────────────────────
        elif address == 0x0A: self.ctrlpf = value

        # ── 0x0B-0x0C  REFP0, REFP1  (bit 3) ────────────────────────────────
        elif address == 0x0B: self.refp0 = bool(value & 0x08)
        elif address == 0x0C: self.refp1 = bool(value & 0x08)

        # ── 0x0D-0x0F  Playfield data ─────────────────────────────────────────
        elif address == 0x0D: self.pf0 = value
        elif address == 0x0E: self.pf1 = value
        elif address == 0x0F: self.pf2 = value

        # ── 0x10-0x14  Horizontal position reset ─────────────────────────────
        elif address == 0x10: self._reset_pos('p0')
        elif address == 0x11: self._reset_pos('p1')
        elif address == 0x12: self._reset_pos('m0')
        elif address == 0x13: self._reset_pos('m1')
        elif address == 0x14: self._reset_pos('bl')

        # ── 0x15-0x1A  Audio ─────────────────────────────────────────────────
        elif address == 0x15: self.audc[0] = value & 0x0F
        elif address == 0x16: self.audc[1] = value & 0x0F
        elif address == 0x17: self.audf[0] = value & 0x1F
        elif address == 0x18: self.audf[1] = value & 0x1F
        elif address == 0x19: self.audv[0] = value & 0x0F
        elif address == 0x1A: self.audv[1] = value & 0x0F

        # ── 0x1B  GRP0  (also latches current GRP1 into delay reg) ───────────
        elif address == 0x1B:
            self._grp1d = self.grp1
            self.grp0   = value

        # ── 0x1C  GRP1  (latches GRP0 delay, commits delayed ENABL) ──────────
        elif address == 0x1C:
            self._grp0d = self.grp0
            self.grp1   = value
            self.enabl  = self._enabld   # commit delayed ball enable

        # ── 0x1D-0x1F  Object enable ─────────────────────────────────────────
        elif address == 0x1D: self.enam0  = bool(value & 0x02)
        elif address == 0x1E: self.enam1  = bool(value & 0x02)
        elif address == 0x1F: self._enabld = bool(value & 0x02)   # ENABL (delayed)

        # ── 0x20-0x24  Fine motion (upper nibble only) ────────────────────────
        elif address == 0x20: self.hmp0 = value >> 4
        elif address == 0x21: self.hmp1 = value >> 4
        elif address == 0x22: self.hmm0 = value >> 4
        elif address == 0x23: self.hmm1 = value >> 4
        elif address == 0x24: self.hmbl = value >> 4

        # ── 0x25-0x27  Vertical delay ─────────────────────────────────────────
        elif address == 0x25: self.vdelp0 = bool(value & 0x01)
        elif address == 0x26: self.vdelp1 = bool(value & 0x01)
        elif address == 0x27: self.vdelbl = bool(value & 0x01)

        # ── 0x28-0x29  Reset missile to player ───────────────────────────────
        elif address == 0x28: self.resmp0 = bool(value & 0x02)
        elif address == 0x29: self.resmp1 = bool(value & 0x02)

        # ── 0x2A  HMOVE ───────────────────────────────────────────────────────
        elif address == 0x2A:
            self._apply_hmove()
            self._hmove_blank_ctr = 8

        # ── 0x2B  HMCLR ───────────────────────────────────────────────────────
        elif address == 0x2B:
            self.hmp0 = self.hmp1 = 0
            self.hmm0 = self.hmm1 = 0
            self.hmbl = 0

        # ── 0x2C  CXCLR ───────────────────────────────────────────────────────
        elif address == 0x2C:
            for k in self._cx:
                self._cx[k] = False

    # =========================================================================
    # Horizontal position reset helper
    # =========================================================================

    def _reset_pos(self, obj: str):
        """
        RESPx/RESMx/RESBL: latch object position to current beam.
        Real hardware has a ~5-pixel pipeline delay from write to effect.
        If written during hblank the object appears near the left edge (pixel 3).
        """
        if self.color_clock < self.HBLANK_CLOCKS:
            pos = 3
        else:
            pos = (self.color_clock - self.HBLANK_CLOCKS + 5) % self.VISIBLE_PIXELS

        if   obj == 'p0': self.resp0 = pos
        elif obj == 'p1': self.resp1 = pos
        elif obj == 'm0': self.resm0 = pos
        elif obj == 'm1': self.resm1 = pos
        elif obj == 'bl': self.resbl = pos

    # =========================================================================
    # HMOVE fine motion
    # =========================================================================

    @staticmethod
    def _hm_signed(nibble: int) -> int:
        """
        4-bit HM nibble (stored as raw upper nibble) → signed pixel offset.
        Encoding: 0111=+7 ... 0000=0 ... 1111=-1 ... 1000=-8
        Positive = right, negative = left.
        """
        v = nibble & 0xF
        return v - 16 if v >= 8 else v

    def _apply_hmove(self):
        def shift(pos, nibble):
            # Subtract because positive nibble moves object leftward on screen
            return (pos - self._hm_signed(nibble)) % self.VISIBLE_PIXELS

        self.resp0 = shift(self.resp0, self.hmp0)
        self.resp1 = shift(self.resp1, self.hmp1)
        self.resm0 = shift(self.resm0, self.hmm0)
        self.resm1 = shift(self.resm1, self.hmm1)
        self.resbl = shift(self.resbl, self.hmbl)

        # Missiles locked to players follow the player's new position
        if self.resmp0: self.resm0 = self.resp0
        if self.resmp1: self.resm1 = self.resp1

    # =========================================================================
    # Timing core
    # =========================================================================

    def tick(self):
        """Advance one TIA color clock (called 3× per CPU cycle)."""
        if self.wsync_pending:
            self._advance_clock()
            if self.color_clock == 0:
                self.wsync_pending = False
            return

        self._render_pixel()
        self._advance_clock()

    def _advance_clock(self):
        self.color_clock += 1
        if self.color_clock >= self.COLOR_CLOCKS_PER_SCANLINE:
            self.color_clock = 0
            self.scanline    += 1
            if self.scanline >= self.TOTAL_SCANLINES:
                self.scanline = 0

    # =========================================================================
    # Per-pixel rendering
    # =========================================================================

    def _render_pixel(self):
        cc = self.color_clock
        sl = self.scanline

        if cc < self.HBLANK_CLOCKS:
            return
        if sl < self.VISIBLE_START_LINE or sl >= self.VISIBLE_START_LINE + self.VISIBLE_SCANLINES:
            return

        x = cc - self.HBLANK_CLOCKS
        y = sl - self.VISIBLE_START_LINE

        if self.vblank:
            self._put_pixel(x, y, 0, 0, 0)
            return

        # HMOVE extended left-edge blank bar
        if self._hmove_blank_ctr > 0:
            self._hmove_blank_ctr -= 1
            self._put_pixel(x, y, 0, 0, 0)
            return

        # ── Object activity at this pixel ──────────────────────────────────
        pf_on = self._pf_pixel(x)
        p0_on = self._player_pixel(x, 0)
        p1_on = self._player_pixel(x, 1)
        m0_on = self._missile_pixel(x, 0)
        m1_on = self._missile_pixel(x, 1)
        bl_on = self._ball_pixel(x)

        # ── Collision latches ──────────────────────────────────────────────
        cx = self._cx
        if m0_on:
            if p1_on: cx['M0P1'] = True
            if p0_on: cx['M0P0'] = True
            if pf_on: cx['M0PF'] = True
            if bl_on: cx['M0BL'] = True
        if m1_on:
            if p1_on: cx['M1P1'] = True
            if p0_on: cx['M1P0'] = True
            if pf_on: cx['M1PF'] = True
            if bl_on: cx['M1BL'] = True
        if p0_on:
            if pf_on: cx['P0PF'] = True
            if bl_on: cx['P0BL'] = True
            if p1_on: cx['P0P1'] = True
        if p1_on:
            if pf_on: cx['P1PF'] = True
            if bl_on: cx['P1BL'] = True
        if bl_on and pf_on: cx['BLPF']  = True
        if m0_on and m1_on: cx['M0M1']  = True

        # ── Priority & colour ──────────────────────────────────────────────
        score_mode    = bool(self.ctrlpf & 0x02)
        priority_mode = bool(self.ctrlpf & 0x04)

        pf_color = (self.colup0 if x < 80 else self.colup1) if score_mode else self.colupf

        color = self.colubk

        if priority_mode:
            # PF/BL have highest priority, then P0/M0, then P1/M1
            if p1_on: color = self.colup1
            if m1_on: color = self.colup1
            if p0_on: color = self.colup0
            if m0_on: color = self.colup0
            if bl_on: color = self.colupf
            if pf_on: color = pf_color
        else:
            # Normal: P0/M0 over P1/M1 over PF/BL
            if bl_on: color = self.colupf
            if pf_on: color = pf_color
            if m1_on: color = self.colup1
            if p1_on: color = self.colup1
            if m0_on: color = self.colup0
            if p0_on: color = self.colup0

        r, g, b = _color_rgb(color)
        self._put_pixel(x, y, r, g, b)

    def _put_pixel(self, x: int, y: int, r: int, g: int, b: int):
        base = (y * self.VISIBLE_PIXELS + x) * 4
        self.framebuffer[base    ] = r
        self.framebuffer[base + 1] = g
        self.framebuffer[base + 2] = b
        self.framebuffer[base + 3] = 255

    # =========================================================================
    # Object pixel generators
    # =========================================================================

    def _pf_pixel(self, x: int) -> bool:
        """
        Playfield — 20 bits, each covering 4 pixels = 80 pixels per half.

        Bit ordering (hardware-accurate):
          PF0  bits 4-7 → PF indices 0-3   (bit 4 = leftmost)
          PF1  bits 7-0 → PF indices 4-11  (bit 7 = leftmost)
          PF2  bits 0-7 → PF indices 12-19 (bit 0 = leftmost)

        Right half: reflect if CTRLPF bit 0, else repeat.
        """
        if x < 80:
            idx = x >> 2
        elif self.ctrlpf & 0x01:           # reflect
            idx = (159 - x) >> 2
        else:                              # repeat
            idx = (x - 80) >> 2

        return self._pf_bit(idx)

    def _pf_bit(self, index: int) -> bool:
        """Extract playfield bit at logical index 0-19."""
        if index < 4:
            # PF0: bit 4 = index 0, bit 5 = index 1, bit 6 = index 2, bit 7 = index 3
            return bool(self.pf0 & (1 << (index + 4)))
        elif index < 12:
            # PF1: bit 7 = index 4, bit 6 = index 5, ... bit 0 = index 11
            return bool(self.pf1 & (1 << (11 - index)))
        else:
            # PF2: bit 0 = index 12, bit 1 = index 13, ... bit 7 = index 19
            return bool(self.pf2 & (1 << (index - 12)))

    def _player_pixel(self, x: int, player: int) -> bool:
        """Return True if the player sprite covers pixel x."""
        if player == 0:
            resp, nusiz, refp = self.resp0, self.nusiz0, self.refp0
            gfx = self._grp0d if self.vdelp0 else self.grp0
        else:
            resp, nusiz, refp = self.resp1, self.nusiz1, self.refp1
            gfx = self._grp1d if self.vdelp1 else self.grp1

        if gfx == 0:
            return False

        size_mode = nusiz & 0x07
        stretch   = _NUSIZ_STRETCH.get(size_mode, 1)
        offsets   = _NUSIZ_OFFSETS.get(size_mode, [0])

        for offset in offsets:
            start = (resp + offset) % self.VISIBLE_PIXELS
            dx    = (x - start) % self.VISIBLE_PIXELS
            if 0 <= dx < 8 * stretch:
                bit = dx // stretch        # which bit of the 8-bit graphic (0=left)
                if refp:
                    bit = 7 - bit
                if gfx & (0x80 >> bit):
                    return True
        return False

    def _missile_pixel(self, x: int, missile: int) -> bool:
        """Return True if missile covers pixel x."""
        if missile == 0:
            enabled, pos, nusiz, locked, ppos = (
                self.enam0, self.resm0, self.nusiz0, self.resmp0, self.resp0)
        else:
            enabled, pos, nusiz, locked, ppos = (
                self.enam1, self.resm1, self.nusiz1, self.resmp1, self.resp1)

        if not enabled:
            return False
        if locked:
            pos = ppos

        # Missile width: NUSIZ bits 5-4
        width = _SIZE_WIDTH.get((nusiz >> 4) & 0x03, 1)
        dx = (x - pos) % self.VISIBLE_PIXELS
        return 0 <= dx < width

    def _ball_pixel(self, x: int) -> bool:
        """Return True if ball covers pixel x."""
        active = self._enabld if self.vdelbl else self.enabl
        if not active:
            return False

        # Ball width: CTRLPF bits 5-4
        width = _SIZE_WIDTH.get((self.ctrlpf >> 4) & 0x03, 1)
        dx = (x - self.resbl) % self.VISIBLE_PIXELS
        return 0 <= dx < width

    # =========================================================================
    # Frame management
    # =========================================================================

    def _end_frame(self):
        self.frame       += 1
        self.frame_ready  = True
        self.scanline     = 0
        self.color_clock  = 0

    def consume_frame(self):
        """
        Clear frame_ready and return a copy of the completed framebuffer.
        Format: bytearray, RGBA32, 160 × 192, row-major.
        Returns None if no frame is ready.
        """
        if self.frame_ready:
            self.frame_ready = False
            return bytearray(self.framebuffer)
        return None

    # =========================================================================
    # Audio
    # =========================================================================

    def audio_output(self) -> tuple:
        """Return (volume0, volume1) as 0-15. Waveform synthesis is host-side."""
        return (self.audv[0], self.audv[1])
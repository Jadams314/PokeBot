"""
Pokemon Gen 1 (Red/Blue) PyBoy tile-identifier → character decoder.

PyBoy returns tile identifiers in the range 0–383 (three VRAM blocks).
Pokemon Red/Blue uses signed tile addressing (LCDC bit 4 = 0), so:

  Pokemon char byte 0x80–0xFF  →  PyBoy ID = same value (128–255)
  Pokemon char byte 0x00–0x7F  →  PyBoy ID = 256 + byte  (256–383)

The character tiles (letters, digits, punctuation) all live in the
128–255 range. Blank / space / newline tiles live in 256–383.
"""

# PyBoy tile identifier → printable character
TILE_TO_CHAR = {
    # Uppercase letters (Pokemon 0x80–0x99 = PyBoy 128–153)
    128: 'A', 129: 'B', 130: 'C', 131: 'D', 132: 'E',
    133: 'F', 134: 'G', 135: 'H', 136: 'I', 137: 'J',
    138: 'K', 139: 'L', 140: 'M', 141: 'N', 142: 'O',
    143: 'P', 144: 'Q', 145: 'R', 146: 'S', 147: 'T',
    148: 'U', 149: 'V', 150: 'W', 151: 'X', 152: 'Y',
    153: 'Z',
    # Symbols (Pokemon 0x9A–0x9F = PyBoy 154–159)
    154: '(', 155: ')', 156: ':', 157: ';', 158: '[', 159: ']',
    # Lowercase letters (Pokemon 0xA0–0xB9 = PyBoy 160–185)
    160: 'a', 161: 'b', 162: 'c', 163: 'd', 164: 'e',
    165: 'f', 166: 'g', 167: 'h', 168: 'i', 169: 'j',
    170: 'k', 171: 'l', 172: 'm', 173: 'n', 174: 'o',
    175: 'p', 176: 'q', 177: 'r', 178: 's', 179: 't',
    180: 'u', 181: 'v', 182: 'w', 183: 'x', 184: 'y',
    185: 'z',
    # Extended (Pokemon 0xBA–0xBF = PyBoy 186–191)
    186: 'e', 187: "'d", 188: "'l", 189: "'s", 190: "'t", 191: "'v",
    # Punctuation (Pokemon 0xE0–0xF5 = PyBoy 224–245)
    224: "'", 227: '-', 230: '?', 231: '!', 232: '.',
    242: '$', 243: '*', 245: '/',
    # Digits (Pokemon 0xF6–0xFF = PyBoy 246–255)
    246: '0', 247: '1', 248: '2', 249: '3', 250: '4',
    251: '5', 252: '6', 253: '7', 254: '8', 255: '9',
    # Blank / whitespace / control (Pokemon 0x00–0x7F = PyBoy 256–383)
    256: ' ',   # 0x00 blank tile
    334: ' ',   # 0x4E newline
    335: ' ',   # 0x4F line continuation
    336: ' ',   # 0x50 string terminator
    383: ' ',   # 0x7F space character
}

_DEFAULT = ' '


def decode_tiles(tile_array):
    """Convert a 2D array of PyBoy tile identifiers into a list of strings (one per row)."""
    return [
        ''.join(TILE_TO_CHAR.get(int(t), _DEFAULT) for t in row)
        for row in tile_array
    ]


def readable_text(tile_array):
    """Decode tile array to a compact human-readable string, dropping blank lines."""
    lines = [line.strip() for line in decode_tiles(tile_array)]
    return '  |  '.join(line for line in lines if line)

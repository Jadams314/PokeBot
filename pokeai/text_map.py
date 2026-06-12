"""
Pokemon Gen 1 (Red/Blue) tile-to-character decoder.

When the game renders text it writes tile indices directly to the VRAM
background tilemap — the same indices that identify which character graphic
to draw. Reading the tilemap therefore gives us the exact characters
displayed on screen with no image processing required.
"""

# VRAM tile index → printable character (from the pokered charmap)
TILE_TO_CHAR = {
    # Uppercase letters
    0x80: 'A', 0x81: 'B', 0x82: 'C', 0x83: 'D', 0x84: 'E',
    0x85: 'F', 0x86: 'G', 0x87: 'H', 0x88: 'I', 0x89: 'J',
    0x8A: 'K', 0x8B: 'L', 0x8C: 'M', 0x8D: 'N', 0x8E: 'O',
    0x8F: 'P', 0x90: 'Q', 0x91: 'R', 0x92: 'S', 0x93: 'T',
    0x94: 'U', 0x95: 'V', 0x96: 'W', 0x97: 'X', 0x98: 'Y',
    0x99: 'Z',
    0x9A: '(', 0x9B: ')', 0x9C: ':', 0x9D: ';', 0x9E: '[', 0x9F: ']',
    # Lowercase letters
    0xA0: 'a', 0xA1: 'b', 0xA2: 'c', 0xA3: 'd', 0xA4: 'e',
    0xA5: 'f', 0xA6: 'g', 0xA7: 'h', 0xA8: 'i', 0xA9: 'j',
    0xAA: 'k', 0xAB: 'l', 0xAC: 'm', 0xAD: 'n', 0xAE: 'o',
    0xAF: 'p', 0xB0: 'q', 0xB1: 'r', 0xB2: 's', 0xB3: 't',
    0xB4: 'u', 0xB5: 'v', 0xB6: 'w', 0xB7: 'x', 0xB8: 'y',
    0xB9: 'z',
    0xBA: 'e', 0xBB: "'d", 0xBC: "'l", 0xBD: "'s",
    0xBE: "'t", 0xBF: "'v",
    # Digits
    0xF6: '0', 0xF7: '1', 0xF8: '2', 0xF9: '3', 0xFA: '4',
    0xFB: '5', 0xFC: '6', 0xFD: '7', 0xFE: '8', 0xFF: '9',
    # Whitespace and control codes
    0x7F: ' ',   # space
    0x50: ' ',   # string terminator (renders blank)
    0x4E: ' ',   # newline (we flatten to space for single-line display)
    0x4F: ' ',   # line continuation
    0x00: ' ',   # blank tile
    # Punctuation
    0xE0: "'", 0xE3: '-', 0xE6: '?', 0xE7: '!',
    0xE8: '.', 0xF2: '$', 0xF3: '*', 0xF5: '/',
}

_DEFAULT = ' '


def decode_tiles(tile_array):
    """Convert a 2D array of VRAM tile indices into a list of strings (one per row)."""
    return [
        ''.join(TILE_TO_CHAR.get(int(t), _DEFAULT) for t in row)
        for row in tile_array
    ]


def readable_text(tile_array):
    """Decode tile array to a compact human-readable string, dropping blank lines."""
    lines = [line.strip() for line in decode_tiles(tile_array)]
    return '  |  '.join(line for line in lines if line)

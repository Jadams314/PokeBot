"""
RAM addresses for Pokemon Blue (English, Gen 1).

Pokemon Red and Blue share the same WRAM layout. Addresses come from the
pokered disassembly project (https://github.com/pret/pokered).
"""

# --- Party ---
PARTY_COUNT = 0xD163          # number of pokemon in the party (0-6)
PARTY_MON_STRUCT_START = 0xD16B
PARTY_MON_STRUCT_SIZE = 44
PARTY_LEVEL_OFFSET = 33       # level byte inside each party mon struct
PARTY_HP_OFFSET = 1           # current HP, 2 bytes big-endian
PARTY_MAX_HP_OFFSET = 34      # max HP, 2 bytes big-endian

PARTY_LEVEL_ADDRS = [
    PARTY_MON_STRUCT_START + PARTY_LEVEL_OFFSET + i * PARTY_MON_STRUCT_SIZE
    for i in range(6)
]
PARTY_HP_ADDRS = [
    PARTY_MON_STRUCT_START + PARTY_HP_OFFSET + i * PARTY_MON_STRUCT_SIZE
    for i in range(6)
]
PARTY_MAX_HP_ADDRS = [
    PARTY_MON_STRUCT_START + PARTY_MAX_HP_OFFSET + i * PARTY_MON_STRUCT_SIZE
    for i in range(6)
]

# --- Progress ---
BADGES = 0xD356               # one bit per gym badge (8 bits = 8 badges)
EVENT_FLAGS_START = 0xD747    # story event flags, one bit each
EVENT_FLAGS_LENGTH = 320      # bytes of event flags to scan

POKEDEX_OWNED_START = 0xD2F7  # bitfield, 19 bytes (151 pokemon)
POKEDEX_SEEN_START = 0xD30A   # bitfield, 19 bytes
POKEDEX_BYTES = 19

# --- Location ---
MAP_ID = 0xD35E
PLAYER_Y = 0xD361
PLAYER_X = 0xD362

# Map IDs of interest
MAP_REDS_HOUSE_1F = 37
MAP_REDS_HOUSE_2F = 38
MAP_HALL_OF_FAME = 118        # entering this room == champion defeated

# --- Game completion ---
NUM_HOF_TEAMS = 0xD5A0        # times the player has entered the Hall of Fame

# --- In-game clock (the same clock the game shows on the save screen) ---
PLAY_TIME_HOURS = 0xDA41
PLAY_TIME_MINUTES = 0xDA43
PLAY_TIME_SECONDS = 0xDA44

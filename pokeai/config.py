"""Central configuration: paths and training hyperparameters."""

import os
import torch

# Project layout (everything lives next to play.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROM_DIR = os.path.join(BASE_DIR, "roms")
CHECKPOINT_DIR = os.path.join(BASE_DIR, "checkpoints")
TENSORBOARD_DIR = os.path.join(BASE_DIR, "tensorboard")
INIT_STATE = os.path.join(BASE_DIR, "init.state")
COMPLETIONS_FILE = os.path.join(BASE_DIR, "completions.json")
PROGRESS_FILE = os.path.join(BASE_DIR, "progress.json")

ROM_EXTENSIONS = (".gb", ".gbc")

# --- Environment ---
ACTIONS = ["up", "down", "left", "right", "a", "b", "start"]
ACTION_HOLD_FRAMES = 8        # frames the button is held down
ACTION_WAIT_FRAMES = 16       # frames to let the game react afterwards
FRAME_STACK = 3               # how many past screens the model sees at once
SCREEN_SHAPE = (72, 80)       # downscaled from the Game Boy's 144x160

# Text observation — bottom portion of the background tilemap.
# Rows 12-17 cover the text box (14-17) plus two rows of battle/menu context.
TEXT_ROW_START = 12
TEXT_ROWS = 6
TEXT_COLS = 20

NO_PROGRESS_STEPS = 5000      # episode ends if no new tile visited within this many steps

# --- Rewards (what the model gets "points" for) ---
REWARD_NEW_TILE = 0.01        # stepping somewhere it has never been this episode
REWARD_NEW_MAP = 3.0          # entering a brand new map/area
REWARD_NEW_BUILDING = 5.0     # entering a building for the first time this episode
REWARD_NEW_TEXT = 1.5         # seeing a new unique text string this episode
REWARD_LEVEL = 1.0            # per pokemon level gained
REWARD_BADGE = 20.0           # per gym badge
REWARD_EVENT = 8.0            # per story event flag set
REWARD_DEX_SEEN = 0.2         # per new pokemon seen
REWARD_DEX_OWNED = 3.0        # per new pokemon caught
REWARD_COMPLETION = 500.0     # entering the Hall of Fame (game beaten!)
LEVEL_REWARD_CAP = 120        # stop rewarding levels past this party total

# Tileset IDs that represent indoor buildings (from the pokered disassembly).
# Excludes: 0=Overworld, 3=Forest, 14=Cemetery, 16=Cavern, 22=Plateau.
BUILDING_TILESETS = frozenset({1, 2, 4, 5, 6, 7, 8, 9, 11, 12, 13, 15, 17, 18, 19, 20, 21})

# --- Device ---
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# --- PPO training ---
NUM_ENVS = 8                  # parallel copies of the game (lower if low on RAM)
PPO_N_STEPS = 2048
PPO_BATCH_SIZE = 512
PPO_GAMMA = 0.998
PPO_ENT_COEF = 0.01
PPO_LEARNING_RATE = 2.5e-4
TOTAL_TIMESTEPS = 1_000_000_000   # effectively "train until you stop it"
CHECKPOINT_EVERY_STEPS = 50_000   # per-env steps between auto-saves

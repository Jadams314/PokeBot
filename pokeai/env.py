"""
Gymnasium environment that wraps Pokemon Blue running inside the PyBoy
Game Boy emulator.

The model sees the screen (plus a small stats vector) and can press the
same buttons a human can. It earns reward for exploring, levelling up,
earning badges, advancing the story, and ultimately entering the Hall of
Fame, which counts as beating the game.
"""

import io
import json
import os
import time

import numpy as np
import gymnasium as gym
from gymnasium import spaces
from pyboy import PyBoy

from . import config as C
from . import memory_map as M
from .text_map import readable_text


class PokemonBlueEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(self, rom_path, init_state=None, headless=True,
                 emulation_speed=0, instance_id=0):
        super().__init__()
        self.rom_path = rom_path
        self.init_state = init_state
        self.instance_id = instance_id

        self.pyboy = PyBoy(
            rom_path,
            window="null" if headless else "SDL2",
            sound_emulated=False,
        )
        # 0 = run as fast as the CPU allows, 1 = real-time (for watching)
        self.pyboy.set_emulation_speed(emulation_speed)

        self.action_space = spaces.Discrete(len(C.ACTIONS))
        h, w = C.SCREEN_SHAPE
        self.observation_space = spaces.Dict({
            "screen": spaces.Box(0, 255, (C.FRAME_STACK, h, w), np.uint8),
            "text":   spaces.Box(0.0, 1.0, (C.TEXT_ROWS * C.TEXT_COLS,), np.float32),
            "stats":  spaces.Box(0.0, 1.0, (12,), np.float32),
        })

        self._initial_state_bytes = None
        self._frames = np.zeros((C.FRAME_STACK, h, w), dtype=np.uint8)
        # These persist across episodes — map rewards only fire the first time
        # an env ever visits a new map/building, creating a permanent frontier
        # that advances as the model explores further.
        self.visited_maps = set()
        self.visited_buildings = set()
        self.reset_internal_state()

    # ------------------------------------------------------------------ #
    # Memory helpers
    # ------------------------------------------------------------------ #
    def read(self, addr):
        return self.pyboy.memory[addr]

    def party_levels(self):
        n = min(self.read(M.PARTY_COUNT), 6)
        return [self.read(a) for a in M.PARTY_LEVEL_ADDRS[:n]]

    def party_hp_fraction(self):
        n = min(self.read(M.PARTY_COUNT), 6)
        if n == 0:
            return 1.0
        cur = sum(
            self.read(a) * 256 + self.read(a + 1) for a in M.PARTY_HP_ADDRS[:n]
        )
        mx = sum(
            self.read(a) * 256 + self.read(a + 1)
            for a in M.PARTY_MAX_HP_ADDRS[:n]
        )
        return cur / mx if mx > 0 else 1.0

    def badge_count(self):
        return bin(self.read(M.BADGES)).count("1")

    def event_flag_count(self):
        return sum(
            bin(self.read(M.EVENT_FLAGS_START + i)).count("1")
            for i in range(M.EVENT_FLAGS_LENGTH)
        )

    def dex_counts(self):
        seen = sum(
            bin(self.read(M.POKEDEX_SEEN_START + i)).count("1")
            for i in range(M.POKEDEX_BYTES)
        )
        owned = sum(
            bin(self.read(M.POKEDEX_OWNED_START + i)).count("1")
            for i in range(M.POKEDEX_BYTES)
        )
        return seen, owned

    def position(self):
        return (self.read(M.MAP_ID), self.read(M.PLAYER_X),
                self.read(M.PLAYER_Y))

    def game_completed(self):
        if self.read(M.MAP_ID) == M.MAP_HALL_OF_FAME:
            return True
        return self.read(M.NUM_HOF_TEAMS) > 0

    def in_game_time(self):
        """The same play-time clock the game shows on its save screen."""
        h = self.read(M.PLAY_TIME_HOURS)
        m = self.read(M.PLAY_TIME_MINUTES)
        s = self.read(M.PLAY_TIME_SECONDS)
        return f"{h:02d}:{m:02d}:{s:02d}"

    # ------------------------------------------------------------------ #
    # Gym interface
    # ------------------------------------------------------------------ #
    def reset_internal_state(self):
        self.step_count = 0
        self.steps_since_new_tile = 0
        self.visited_tiles = set()
        self.seen_text = set()
        self._text_tiles = np.zeros((C.TEXT_ROWS, C.TEXT_COLS), dtype=np.int32)
        self.prev_level_sum = 0
        self.prev_badges = 0
        self.prev_events = 0
        self.prev_seen = 0
        self.prev_owned = 0
        self.total_reward = 0.0
        self.episode_start_wall = time.time()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        if self.init_state and os.path.exists(self.init_state):
            with open(self.init_state, "rb") as f:
                self.pyboy.load_state(f)
        elif self._initial_state_bytes is not None:
            # No init state: rewind to power-on so every episode starts equal
            self._initial_state_bytes.seek(0)
            self.pyboy.load_state(self._initial_state_bytes)
        else:
            # First ever reset without an init state: snapshot power-on
            self._initial_state_bytes = io.BytesIO()
            self.pyboy.save_state(self._initial_state_bytes)

        self.reset_internal_state()

        # Take baselines so the first step isn't rewarded for pre-existing
        # progress in the loaded state
        self.prev_level_sum = sum(self.party_levels())
        self.prev_badges = self.badge_count()
        self.prev_events = self.event_flag_count()
        self.prev_seen, self.prev_owned = self.dex_counts()
        self.visited_tiles.add(self.position())
        self.visited_maps.add(self.position()[0])

        self._frames[:] = 0
        self._push_frame()
        self._text_tiles = self._read_text_tiles()
        return self._observation(), {}

    def step(self, action):
        button = C.ACTIONS[action]
        self.pyboy.button_press(button)
        self.pyboy.tick(C.ACTION_HOLD_FRAMES, False)
        self.pyboy.button_release(button)
        self.pyboy.tick(C.ACTION_WAIT_FRAMES - 1, False)
        self.pyboy.tick(1, True)  # render only the final frame

        self.step_count += 1
        self._push_frame()
        self._text_tiles = self._read_text_tiles()

        reward, completed = self._compute_reward()
        self.total_reward += reward

        terminated = completed
        truncated = self.steps_since_new_tile >= C.NO_PROGRESS_STEPS

        info = {
            "badges": self.prev_badges,
            "level_sum": self.prev_level_sum,
            "events": self.prev_events,
            "maps_visited": len(self.visited_maps),
            "buildings_visited": len(self.visited_buildings),
            "tiles_visited": len(self.visited_tiles),
            "dex_seen": self.prev_seen,
            "dex_owned": self.prev_owned,
            "episode_reward": self.total_reward,
            "instance_id": self.instance_id,
        }
        if completed:
            info["completed"] = True
            info["in_game_time"] = self.in_game_time()
            info["episode_steps"] = self.step_count

        return self._observation(), reward, terminated, truncated, info

    def render(self):
        pass  # the SDL2 window renders itself when headless=False

    def close(self):
        self.pyboy.stop(save=False)

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _read_text_tiles(self):
        bg = self.pyboy.tilemap_background
        # PyBoy returns tile identifiers 0-383 (three VRAM blocks); int32 holds this safely.
        return np.array(
            [[bg[col, row] for col in range(C.TEXT_COLS)]
             for row in range(C.TEXT_ROW_START, C.TEXT_ROW_START + C.TEXT_ROWS)],
            dtype=np.int32,
        )

    def _push_frame(self):
        # Screen is 144x160 RGBA; convert to grayscale and halve resolution
        rgba = self.pyboy.screen.ndarray
        gray = rgba[:, :, :3].mean(axis=2).astype(np.uint8)
        small = gray[::2, ::2]
        self._frames = np.roll(self._frames, shift=-1, axis=0)
        self._frames[-1] = small

    def _observation(self):
        levels = self.party_levels()
        stats = np.zeros(12, dtype=np.float32)
        stats[0] = self.prev_badges / 8.0
        stats[1] = min(sum(levels) / 600.0, 1.0)
        stats[2] = self.party_hp_fraction()
        stats[3] = min(len(self.visited_tiles) / 20000.0, 1.0)
        stats[4] = min(self.prev_events / 1000.0, 1.0)
        stats[5] = min(self.prev_owned / 151.0, 1.0)
        for i, lv in enumerate(levels[:6]):
            stats[6 + i] = min(lv / 100.0, 1.0)
        return {
            "screen": self._frames.copy(),
            "text":   self._text_tiles.astype(np.float32).flatten() / 383.0,
            "stats":  stats,
        }

    def _compute_reward(self):
        reward = 0.0

        pos = self.position()
        map_id = pos[0]
        if pos not in self.visited_tiles:
            self.visited_tiles.add(pos)
            reward += C.REWARD_NEW_TILE
            self.steps_since_new_tile = 0
        else:
            self.steps_since_new_tile += 1
        if map_id not in self.visited_maps:
            self.visited_maps.add(map_id)
            reward += C.REWARD_NEW_MAP
        if (map_id not in self.visited_buildings
                and self.read(M.MAP_TILESET) in C.BUILDING_TILESETS):
            self.visited_buildings.add(map_id)
            reward += C.REWARD_NEW_BUILDING

        text = readable_text(self._text_tiles)
        if text and text not in self.seen_text:
            self.seen_text.add(text)
            reward += C.REWARD_NEW_TEXT
            self.steps_since_new_tile = 0

        level_sum = sum(self.party_levels())
        if level_sum > self.prev_level_sum and self.prev_level_sum < C.LEVEL_REWARD_CAP:
            reward += C.REWARD_LEVEL * (level_sum - self.prev_level_sum)
        self.prev_level_sum = max(level_sum, self.prev_level_sum)

        badges = self.badge_count()
        if badges > self.prev_badges:
            reward += C.REWARD_BADGE * (badges - self.prev_badges)
            self.prev_badges = badges

        # Event flags are expensive to scan, so only check periodically
        if self.step_count % 32 == 0:
            events = self.event_flag_count()
            if events > self.prev_events:
                reward += C.REWARD_EVENT * (events - self.prev_events)
                self.prev_events = events

            seen, owned = self.dex_counts()
            if seen > self.prev_seen:
                reward += C.REWARD_DEX_SEEN * (seen - self.prev_seen)
                self.prev_seen = seen
            if owned > self.prev_owned:
                reward += C.REWARD_DEX_OWNED * (owned - self.prev_owned)
                self.prev_owned = owned

        completed = self.game_completed()
        if completed:
            reward += C.REWARD_COMPLETION

        return reward, completed

"""
Watch mode: opens a real game window and lets the most recently trained
model play live, at normal Game Boy speed. Run it while training is going
on (or after) to see what the model has learned so far.
"""

import os
import signal
import time

from stable_baselines3 import PPO

from . import config as C
from .env import PokemonBlueEnv
from .train import latest_checkpoint


def watch(rom_path, speed=1):
    checkpoint = latest_checkpoint()
    if checkpoint is None:
        print("No trained model found yet. Start training first with:")
        print("    python play.py")
        return

    print(f"Loading model: {os.path.relpath(checkpoint)}")
    print("Opening game window — press Ctrl+C in this terminal to stop.")
    print("(Tip: re-run this later; it always loads the newest checkpoint.)")

    env = PokemonBlueEnv(
        rom_path,
        init_state=C.INIT_STATE if os.path.exists(C.INIT_STATE) else None,
        headless=False,
        emulation_speed=speed,
    )
    model = PPO.load(checkpoint, device=C.DEVICE)

    _stop = False

    def _handle_sigint(sig, frame):
        nonlocal _stop
        _stop = True

    signal.signal(signal.SIGINT, _handle_sigint)

    try:
        obs, _ = env.reset()
        last_report = time.time()
        games = 1
        while not _stop:
            action, _ = model.predict(obs, deterministic=False)
            obs, _, terminated, truncated, info = env.step(int(action))

            if time.time() - last_report > 30:
                last_report = time.time()
                print(f"  game {games} | badges {info['badges']}/8 | "
                      f"party levels {info['level_sum']} | "
                      f"areas {info['maps_visited']} | "
                      f"buildings {info['buildings_visited']} | "
                      f"points {info['episode_reward']:.0f} | "
                      f"in-game time {env.in_game_time()}")

            if info.get("completed"):
                print("\nThe model just BEAT THE GAME while you watched!")
                print(f"In-game time: {info['in_game_time']}")
            if terminated or truncated:
                games += 1
                obs, _ = env.reset()
    finally:
        env.close()
        print("\nStopped watching. Training checkpoints are unaffected.")

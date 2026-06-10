"""
Watch mode: opens a real game window and lets the most recently trained
model play live, at normal Game Boy speed. Run it while training is going
on (or after) to see what the model has learned so far.
"""

import os
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
    model = PPO.load(checkpoint)

    try:
        obs, _ = env.reset()
        last_report = time.time()
        while True:
            action, _ = model.predict(obs, deterministic=False)
            obs, _, terminated, truncated, info = env.step(int(action))

            if time.time() - last_report > 30:
                last_report = time.time()
                print(f"  badges {info['badges']}/8 | party levels "
                      f"{info['level_sum']} | areas seen "
                      f"{info['maps_visited']} | in-game time "
                      f"{env.in_game_time()}")

            if info.get("completed"):
                print("\nThe model just BEAT THE GAME while you watched!")
                print(f"In-game time: {info['in_game_time']}")
            if terminated or truncated:
                obs, _ = env.reset()
    except KeyboardInterrupt:
        print("\nStopped watching. Training checkpoints are unaffected.")
    finally:
        env.close()

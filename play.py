#!/usr/bin/env python3
"""
Pokemon Blue AI — one-command launcher.

    python play.py            start (or resume) training the AI
    python play.py watch      watch the AI play live in a game window
    python play.py setup      play the 2-minute intro yourself for a
                              better starting point (optional)

Put your Pokemon Blue ROM (.gb file) in the  roms/  folder first.
Missing Python packages are installed automatically on first run.
"""

import argparse
import importlib.util
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROM_DIR = os.path.join(BASE_DIR, "roms")


def ensure_dependencies():
    """Install requirements automatically the first time."""
    missing = [
        pkg for pkg, module in
        [("pyboy", "pyboy"), ("stable-baselines3", "stable_baselines3"),
         ("gymnasium", "gymnasium"), ("torch", "torch"), ("numpy", "numpy")]
        if importlib.util.find_spec(module) is None
    ]
    if not missing:
        return
    print(f"First-time setup: installing {', '.join(missing)} "
          "(this can take a few minutes)...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r",
         os.path.join(BASE_DIR, "requirements.txt")]
    )
    if result.returncode != 0:
        print("\nAutomatic install failed. Please run this yourself:")
        print(f"    {sys.executable} -m pip install -r requirements.txt")
        sys.exit(1)
    print("All packages installed.\n")


def find_rom():
    os.makedirs(ROM_DIR, exist_ok=True)
    roms = [
        os.path.join(ROM_DIR, f)
        for f in sorted(os.listdir(ROM_DIR))
        if f.lower().endswith((".gb", ".gbc"))
    ]
    if not roms:
        print("=" * 64)
        print("  No ROM found!")
        print("=" * 64)
        print(f"""
  Copy your Pokemon Blue ROM file (it ends in .gb) into:

      {ROM_DIR}{os.sep}

  then run  python play.py  again.

  Note: you need to legally own the game and provide your own ROM —
  this project does not include or download one.
""")
        sys.exit(1)
    if len(roms) > 1:
        print(f"Found {len(roms)} ROMs; using {os.path.basename(roms[0])}")
    return roms[0]


def main():
    parser = argparse.ArgumentParser(
        description="An AI that teaches itself to play Pokemon Blue.")
    parser.add_argument(
        "mode", nargs="?", default="train",
        choices=["train", "watch", "setup"],
        help="train (default): start/resume learning | "
             "watch: see the AI play live | "
             "setup: play the intro yourself once for a better start")
    parser.add_argument(
        "--show", action="store_true",
        help="while training, also open a window showing one of the "
             "games being played (runs faster than real time)")
    parser.add_argument(
        "--envs", type=int, default=None,
        help="number of games to play in parallel (default 8; lower this "
             "if your computer struggles)")
    args = parser.parse_args()

    ensure_dependencies()
    rom = find_rom()
    print(f"Using ROM: {os.path.basename(rom)}\n")

    # Imported here so dependency auto-install can happen first
    from pokeai import config as C
    from pokeai.bootstrap import ensure_init_state, manual_setup
    from pokeai.train import train
    from pokeai.watch import watch

    if args.mode == "setup":
        manual_setup(rom)
    elif args.mode == "watch":
        watch(rom)
    else:
        ensure_init_state(rom)
        train(rom, num_envs=args.envs or C.NUM_ENVS, show_window=args.show)


if __name__ == "__main__":
    main()

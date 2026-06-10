"""
Creates `init.state` — a snapshot of the game just after the intro/naming
screens. Training episodes restart from this snapshot so the model doesn't
waste time re-watching the intro thousands of times.

Two ways to make it:

  1. automatic_bootstrap()  - a scripted sequence of button presses that
     skips the intro and picks preset names. Verified afterwards; if the
     timing doesn't line up on your ROM revision it simply reports failure
     and training falls back to starting from power-on (slower but fine).

  2. manual_setup() - opens a playable window. You play the first two
     minutes yourself (intro, names, walk into the grass, receive your
     starter pokemon) and the snapshot is saved automatically the moment
     a pokemon enters your party. This gives the model the best start.
"""

import os

from pyboy import PyBoy

from . import config as C
from . import memory_map as M


def _press(pyboy, button, hold=8, wait=16):
    pyboy.button_press(button)
    pyboy.tick(hold, False)
    pyboy.button_release(button)
    pyboy.tick(wait, False)


def automatic_bootstrap(rom_path, out_path=None, verbose=True):
    """Try to script past the intro. Returns True on success."""
    out_path = out_path or C.INIT_STATE
    if verbose:
        print("Attempting to skip the game intro automatically...")

    pyboy = PyBoy(rom_path, window="null", sound_emulated=False)
    pyboy.set_emulation_speed(0)
    try:
        pyboy.tick(600, False)            # boot logos / intro animation
        for _ in range(4):                # reach title screen and pass it
            _press(pyboy, "start", wait=60)
        _press(pyboy, "a", wait=90)       # select NEW GAME

        # Oak's speech: B advances dialog but can't select menu options,
        # so over-pressing is safe. The naming menus need DOWN + A to pick
        # a preset name.
        for _ in range(160):              # speech up to player naming
            _press(pyboy, "b", wait=10)
        _press(pyboy, "down", wait=30)
        _press(pyboy, "a", wait=60)       # pick preset player name
        for _ in range(120):              # speech up to rival naming
            _press(pyboy, "b", wait=10)
        _press(pyboy, "down", wait=30)
        _press(pyboy, "a", wait=60)       # pick preset rival name
        for _ in range(140):              # rest of speech + shrink animation
            _press(pyboy, "b", wait=10)
        pyboy.tick(120, False)

        map_id = pyboy.memory[M.MAP_ID]
        ok = map_id in (M.MAP_REDS_HOUSE_1F, M.MAP_REDS_HOUSE_2F)
        if ok:
            with open(out_path, "wb") as f:
                pyboy.save_state(f)
            if verbose:
                print(f"Intro skipped! Starting snapshot saved to {out_path}")
        elif verbose:
            print("Automatic intro skip didn't land where expected "
                  f"(map id {map_id}).")
            print("Training will start from the title screen instead — "
                  "that still works, just a bit slower.")
            print("Tip: run  python play.py setup  to play through the "
                  "intro yourself once (about 2 minutes) for a better start.")
        return ok
    finally:
        pyboy.stop(save=False)


def manual_setup(rom_path, out_path=None):
    """Open a playable window; auto-save once the player owns a pokemon."""
    out_path = out_path or C.INIT_STATE
    print()
    print("=" * 64)
    print("  MANUAL SETUP — play the first couple of minutes yourself")
    print("=" * 64)
    print("""
  A game window will open. Controls:
      Arrow keys = D-pad      Z = A button      X = B button
      Enter = Start           Backspace = Select

  Just play normally:
    1. Start a new game, pick any names
    2. Walk out of the house into the tall grass
    3. Follow Professor Oak and take your starter pokemon

  The moment a pokemon joins your party, your progress is saved
  automatically and the window closes. That's it!
""")
    pyboy = PyBoy(rom_path, window="SDL2", sound_emulated=True)
    pyboy.set_emulation_speed(1)
    try:
        while pyboy.tick(1, True):
            if pyboy.memory[M.PARTY_COUNT] not in (0, 0xFF):
                # Let the current dialog settle before snapshotting
                pyboy.tick(120, True)
                with open(out_path, "wb") as f:
                    pyboy.save_state(f)
                print(f"\nGot your starter! Snapshot saved to {out_path}")
                print("You can now run:  python play.py")
                return True
        print("\nWindow closed before a pokemon was obtained — no snapshot "
              "saved.")
        return False
    finally:
        pyboy.stop(save=False)


def ensure_init_state(rom_path):
    """Make sure an init.state exists; try the automatic skip if not."""
    if os.path.exists(C.INIT_STATE):
        return True
    return automatic_bootstrap(rom_path)

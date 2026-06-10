# Pokemon Blue AI

An AI that **teaches itself to play Pokemon Blue** through trial and error
(reinforcement learning). You give it the game; it plays thousands of
lifetimes at high speed, slowly figuring out how to explore, battle, win
badges, and — given enough training — reach the Hall of Fame. When it
beats the game, the completion time is recorded automatically.

You don't need to know anything about AI to use it.

## Quick start (3 steps)

1. **Install Python 3.10 or newer** from <https://python.org> if you don't
   have it (during install, tick "Add Python to PATH").

2. **Add your ROM.** Copy your Pokemon Blue ROM file (ends in `.gb`) into
   the `roms/` folder. You must own the game and supply your own ROM —
   none is included or downloaded.

3. **Press play:**

   ```
   python play.py
   ```

That's it. The first run installs everything it needs, skips the game's
intro automatically, and starts training. Progress is saved constantly —
stop any time with `Ctrl+C` and it picks up where it left off the next
time you run `python play.py`.

## Watching the AI play (live)

Any time — even while training is running in another terminal — open a
real game window and watch the newest version of the AI play at normal
Game Boy speed:

```
python play.py watch
```

Early on it will look like random button mashing. That's genuinely how it
learns: it tries everything, and the behaviors that earn reward (new
places, levels, badges) get reinforced. Re-run `watch` after a few hours
or days of training and you'll see real progress.

You can also add a window to the training itself with
`python play.py --show` (this one runs much faster than real time).

## Checking progress

- A status line prints in the training terminal every ~10,000 steps:
  best badge count, party levels, areas discovered, pokemon caught.
- `progress.json` always holds the latest snapshot.
- For graphs: `tensorboard --logdir tensorboard` then open the printed URL.

## Completion times

The moment the AI enters the Hall of Fame, a record is appended to
`completions.json` with:

- **in-game time** — the same clock the game shows on its save screen,
  i.e. the AI's "speedrun time" for that playthrough
- total training time and training steps it took to get there
- badges and party levels at the finish

A big banner also prints in the training terminal.

## Optional: a better starting point

By default the AI starts from your bedroom (the intro is skipped
automatically). For a slightly better start, play the first two minutes
yourself once:

```
python play.py setup
```

A window opens (arrow keys + `Z` = A, `X` = B, `Enter` = Start). Start a
new game, walk into the grass, take your starter from Professor Oak — the
snapshot saves itself the moment the pokemon joins your party.

## Honest expectations

Learning Pokemon from pixels is a famously hard AI problem. Within hours
the AI typically learns to leave Pallet Town and explore; badges take
days; getting deep into the game can take **weeks of continuous training**
on a normal PC, and reaching the Hall of Fame is not guaranteed — this is
the same challenge that well-known research projects (like the "Pokemon
Red Experiments" this design follows) have spent enormous compute on. The
fun is watching it improve. Leave it running, peek in with
`python play.py watch`, and check `progress.json`.

Tips:
- More parallel games = faster learning: `python play.py --envs 16`
  (needs a beefier CPU/RAM; default is 8, use `--envs 4` on weak machines).
- Keep the same `checkpoints/` folder — that's the AI's brain. Delete it
  only if you want to start from scratch.

## How it works (the short version)

- **Emulator:** [PyBoy](https://github.com/Baekalfen/PyBoy) runs the game
  in Python, headless and faster than real time.
- **What the AI sees:** the last 3 screens (downscaled, grayscale) plus a
  few numbers read from the game's memory (badges, levels, HP).
- **What it can do:** press Up/Down/Left/Right/A/B/Start, like a player.
- **Rewards:** small points for reaching new tiles and new areas, bigger
  points for level-ups, story events, catching pokemon, badges (+20 each),
  and a huge bonus (+500) for entering the Hall of Fame.
- **Learning algorithm:** PPO (Proximal Policy Optimization) from
  Stable-Baselines3, with 8 games running in parallel.
- **Files it creates:** `checkpoints/` (the trained model, auto-resumed),
  `init.state` (post-intro snapshot), `progress.json`, `completions.json`,
  `tensorboard/` (graphs).

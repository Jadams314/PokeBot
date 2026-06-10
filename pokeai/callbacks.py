"""
Training callbacks: console progress reports, a progress.json snapshot you
can peek at any time, and permanent recording of game completions (with
times) into completions.json.
"""

import json
import os
import time
from datetime import datetime

from stable_baselines3.common.callbacks import BaseCallback

from . import config as C


def _fmt_duration(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h >= 24:
        d, h = divmod(h, 24)
        return f"{d}d {h:02d}h {m:02d}m"
    return f"{h:02d}h {m:02d}m {s:02d}s"


class ProgressCallback(BaseCallback):
    """Prints a human-friendly status line and records completions."""

    def __init__(self, report_every_steps=10_000, verbose=0):
        super().__init__(verbose)
        self.report_every_steps = report_every_steps
        self.start_time = time.time()
        self.best = {"badges": 0, "level_sum": 0, "maps_visited": 0,
                     "events": 0, "dex_owned": 0}
        self.completions = 0
        self._next_report = report_every_steps

    def _on_training_start(self):
        print()
        print("Training started. The model is now playing Pokemon Blue.")
        print("  - Watch it live any time:   python play.py watch")
        print("  - Detailed graphs:          tensorboard --logdir "
              f"{os.path.relpath(C.TENSORBOARD_DIR)}")
        print("  - Stop safely with Ctrl+C (progress is saved; it resumes "
              "automatically next run)")
        print()

    def _on_step(self):
        for info in self.locals.get("infos", []):
            improved = False
            for key in self.best:
                if info.get(key, 0) > self.best[key]:
                    self.best[key] = info[key]
                    improved = True
            if improved:
                self.logger.record("pokemon/best_badges", self.best["badges"])
                self.logger.record("pokemon/best_level_sum",
                                   self.best["level_sum"])
                self.logger.record("pokemon/best_maps", self.best["maps_visited"])

            if info.get("completed"):
                self._record_completion(info)

        if self.num_timesteps >= self._next_report:
            self._next_report += self.report_every_steps
            self._report()
        return True

    def _report(self):
        elapsed = _fmt_duration(time.time() - self.start_time)
        b = self.best
        line = (f"[{elapsed} | {self.num_timesteps:,} steps] best so far: "
                f"{b['badges']}/8 badges, party levels {b['level_sum']}, "
                f"{b['maps_visited']} areas, {b['dex_owned']} pokemon caught")
        if self.completions:
            line += f", GAME COMPLETED x{self.completions}!"
        print(line)

        snapshot = dict(b)
        snapshot.update({
            "total_steps": self.num_timesteps,
            "training_time": elapsed,
            "completions": self.completions,
            "updated": datetime.now().isoformat(timespec="seconds"),
        })
        try:
            with open(C.PROGRESS_FILE, "w") as f:
                json.dump(snapshot, f, indent=2)
        except OSError:
            pass

    def _record_completion(self, info):
        self.completions += 1
        record = {
            "completed_at": datetime.now().isoformat(timespec="seconds"),
            "in_game_time": info.get("in_game_time", "unknown"),
            "episode_steps": info.get("episode_steps"),
            "total_training_steps": self.num_timesteps,
            "total_training_time": _fmt_duration(time.time() - self.start_time),
            "badges": info.get("badges"),
            "party_level_sum": info.get("level_sum"),
        }

        records = []
        if os.path.exists(C.COMPLETIONS_FILE):
            try:
                with open(C.COMPLETIONS_FILE) as f:
                    records = json.load(f)
            except (OSError, json.JSONDecodeError):
                records = []
        records.append(record)
        with open(C.COMPLETIONS_FILE, "w") as f:
            json.dump(records, f, indent=2)

        banner = "*" * 64
        print(f"\n{banner}")
        print("  THE MODEL BEAT POKEMON BLUE — HALL OF FAME REACHED!")
        print(f"  In-game completion time : {record['in_game_time']}")
        print(f"  Total training time     : {record['total_training_time']}")
        print(f"  Recorded in {os.path.relpath(C.COMPLETIONS_FILE)}")
        print(f"{banner}\n")

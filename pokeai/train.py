"""
Training entry point: builds parallel game environments, creates or resumes
a PPO model, and trains until interrupted. Everything auto-saves and
auto-resumes, so Ctrl+C is always safe.
"""

import glob
import os

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv

from . import config as C
from .callbacks import ProgressCallback
from .env import PokemonBlueEnv


def make_env(rom_path, instance_id, headless=True):
    def _init():
        env = PokemonBlueEnv(
            rom_path,
            init_state=C.INIT_STATE if os.path.exists(C.INIT_STATE) else None,
            headless=headless,
            instance_id=instance_id,
        )
        return Monitor(env)
    return _init


def latest_checkpoint():
    files = glob.glob(os.path.join(C.CHECKPOINT_DIR, "*.zip"))
    return max(files, key=os.path.getmtime) if files else None


def train(rom_path, num_envs=C.NUM_ENVS, show_window=False):
    os.makedirs(C.CHECKPOINT_DIR, exist_ok=True)
    os.makedirs(C.TENSORBOARD_DIR, exist_ok=True)

    if num_envs > 1:
        env_fns = [
            make_env(rom_path, i, headless=not (show_window and i == 0))
            for i in range(num_envs)
        ]
        vec_env = SubprocVecEnv(env_fns)
    else:
        vec_env = DummyVecEnv([make_env(rom_path, 0, headless=not show_window)])

    resume_from = latest_checkpoint()
    if resume_from:
        print(f"Resuming training from {os.path.relpath(resume_from)}")
        model = PPO.load(resume_from, env=vec_env,
                         tensorboard_log=C.TENSORBOARD_DIR)
    else:
        print("Starting a brand new model (it knows nothing yet — early "
              "play will look completely random; that's normal).")
        model = PPO(
            "MultiInputPolicy",
            vec_env,
            n_steps=C.PPO_N_STEPS,
            batch_size=C.PPO_BATCH_SIZE,
            gamma=C.PPO_GAMMA,
            ent_coef=C.PPO_ENT_COEF,
            learning_rate=C.PPO_LEARNING_RATE,
            tensorboard_log=C.TENSORBOARD_DIR,
            verbose=0,
        )

    callbacks = [
        ProgressCallback(),
        CheckpointCallback(
            save_freq=max(C.CHECKPOINT_EVERY_STEPS // num_envs, 1),
            save_path=C.CHECKPOINT_DIR,
            name_prefix="pokemon_blue",
        ),
    ]

    try:
        model.learn(
            total_timesteps=C.TOTAL_TIMESTEPS,
            callback=callbacks,
            reset_num_timesteps=resume_from is None,
        )
    except KeyboardInterrupt:
        print("\nStopping... saving progress first.")
    finally:
        final_path = os.path.join(C.CHECKPOINT_DIR, "pokemon_blue_latest")
        model.save(final_path)
        try:
            vec_env.close()
        except (EOFError, BrokenPipeError, OSError):
            pass
        print(f"Progress saved to {os.path.relpath(final_path)}.zip")
        print("Run  python play.py  again any time to continue training.")

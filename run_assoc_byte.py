"""
Helper launcher for assoc_byte synth run with baked-in settings.
Runs tournament_phase6 in synth-only mode (no MNIST/download), with sharding/traction on
and checkpoints every 100 steps.
"""
import os
import runpy


def main() -> None:
    env = {
        # data/run mode
        "TP6_RESUME": "0",
        "TP6_SYNTH": "1",
        "TP6_SYNTH_ONLY": "1",
        "TP6_SEQ_MNIST": "0",
        "TP6_OFFLINE_ONLY": "1",
        "TP6_SYNTH_MODE": "assoc_byte",
        "TP6_SYNTH_LEN": "512",
        "TP6_ASSOC_KEYS": "64",
        "TP6_ASSOC_PAIRS": "4",
        "TP6_MAX_SAMPLES": "8192",
        "TP6_BATCH_SIZE": "152",
        "TP6_MAX_STEPS": "20000",
        # scale / AGC
        "TP6_SCALE_INIT": "0.0005",
        "TP6_SCALE_MIN": "0.0005",
        "TP6_SCALE_MAX": "1.0",
        # checkpoint cadence
        "TP6_SAVE_EVERY_STEPS": "100",
        # (shard/traction defaults are now on in code, but keep explicit)
        "TP6_SHARD_BATCH": "1",
        "TP6_SHARD_ADAPT": "1",
        "TP6_TRACTION_LOG": "1",
        # kinetic tempering on by default in code; keep explicit if desired:
        "TP6_DWELL_INERTIA": "1",
    }
    os.environ.update(env)
    runpy.run_module("tournament_phase6", run_name="__main__")


if __name__ == "__main__":
    main()

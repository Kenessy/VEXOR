import os
import time

# --- VRAXION INFINITE ENGINE WRAPPER v1.0 ---
# Runs the kernel indefinitely and restarts on crash.


def bootstrap_env():
    # Hardcode env to avoid shell-quoting failures.
    os.environ["TP6_RESUME"] = "1"
    os.environ["TP6_CKPT"] = "checkpoint.pt"
    os.environ["TP6_SYNTH"] = "1"
    os.environ["TP6_SYNTH_ONLY"] = "1"
    os.environ["TP6_SEQ_MNIST"] = "0"
    os.environ["TP6_OFFLINE_ONLY"] = "1"
    os.environ["TP6_SYNTH_MODE"] = "assoc_byte"
    os.environ["TP6_SYNTH_LEN"] = "512"
    os.environ["TP6_ASSOC_KEYS"] = "64"
    os.environ["TP6_ASSOC_PAIRS"] = "4"
    os.environ["TP6_MAX_SAMPLES"] = "8192"
    os.environ["TP6_BATCH_SIZE"] = "152"
    os.environ["TP6_MAX_STEPS"] = "999999999"
    os.environ["TP6_UPDATE_SCALE"] = "0.05"
    os.environ["TP6_SCALE_INIT"] = "0.05"
    os.environ["TP6_SCALE_MIN"] = "0.000001"
    os.environ["TP6_SCALE_MAX"] = "1.0"
    os.environ["TP6_PTR_INERTIA_OVERRIDE"] = "0.5"
    os.environ["TP6_FORCE_CADENCE_1"] = "1"
    os.environ["TP6_PTR_UPDATE_GOV"] = "0"
    os.environ["TP6_PTR_UPDATE_AUTO"] = "0"
    os.environ["TP6_PTR_UPDATE_EVERY"] = "1"
    os.environ["TP6_PTR_VEL"] = "0"
    os.environ["TP6_SHARD_ADAPT"] = "1"
    os.environ["TP6_SHARD_ADAPT_EVERY"] = "1"
    os.environ["TP6_TRACTION_LOG"] = "1"
    os.environ["TP6_STATE_DECAY"] = "1.0"
    os.environ["TP6_AGC_PLATEAU_WINDOW"] = "0"
    os.environ["TP6_GRAD_CLIP"] = "0"
    os.environ["TP6_XRAY"] = "0"
    os.environ["TP6_SAVE_EVERY_STEPS"] = "100"


def main():
    print("=" * 60)
    print("VRAXION // INFINITE_ENGINE_v1.0")
    print("STATUS: KERNEL_PURIFIED | IGNITION_LOCKED")
    print("=" * 60)

    bootstrap_env()

    try:
        import tournament_phase6 as tp6
        run_fn = getattr(tp6, "tournament_phase6_main", getattr(tp6, "main", None))
        if not run_fn:
            print("[FATAL] Could not find 'main' or 'tournament_phase6_main' in the kernel.")
            return
    except ImportError as e:
        print(f"[FATAL] Failed to import tournament_phase6.py: {e}")
        return

    iteration = 0
    while True:
        iteration += 1
        try:
            if iteration > 1:
                print(f"\n[SYSTEM] Re-Ignition Sequence #{iteration} Initiated...")
                os.environ["TP6_RESUME"] = "1"
            run_fn()
        except KeyboardInterrupt:
            print("\n[USER_STOP] Manual shutdown detected. Powering down.")
            break
        except Exception as e:
            print(f"\n[KINETIC_SHOCK] Kernel Crash Detected: {e}")
            print("Engine restarting in 3 seconds...")
            time.sleep(3)
            continue


if __name__ == "__main__":
    main()

"""VRA-35 helper: print SAFE_START and MAX batch for a workload combo.

This does not modify the probe harness; it is intended for later sweep tooling.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

def _bootstrap_import_path() -> None:
    """Ensure Golden Draft + Golden Code are importable for standalone runs."""

    draftr = Path(__file__).resolve().parents[1]
    reproo = draftr.parent

    if str(draftr) not in sys.path:
        sys.path.insert(0, str(draftr))

    candls: list[str] = []
    for keystr in ("VRAXION_GOLDEN_SRC", "GOLDEN_CODE_ROOT", "GOLDEN_CODE_PATH", "GOLDEN_CODE_DIR"):
        envval = os.environ.get(keystr)
        if envval:
            candls.append(envval)

    candls.append(str(reproo / "Golden Code"))
    candls.append(r"S:\AI\Golden Code")
    candls.append(r"S:/AI/Golden Code")

    for candpt in candls:
        try:
            if candpt and os.path.isdir(candpt):
                if candpt not in sys.path:
                    sys.path.insert(0, candpt)
                break
        except OSError:
            continue


_bootstrap_import_path()


from tools import gpu_capacity_model


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Pick SAFE_START and MAX batch from VRA-35 capacity model.")
    ap.add_argument("--ant", required=True, help="Path to workload spec JSON (ant_spec source).")
    ap.add_argument("--colony", required=True, help="Path to workload spec JSON (colony_spec source).")
    ap.add_argument(
        "--model",
        default=str(Path("Golden Draft") / "tools" / "capacity_model_v1.json"),
        help="Capacity model JSON path.",
    )
    ap.add_argument("--guard-ratio", type=float, default=None, help="Override guard ratio (default: model.guard_ratio).")
    ap.add_argument(
        "--total-vram-bytes",
        type=int,
        default=None,
        help="Runtime total VRAM bytes (required unless --env-json provides it).",
    )
    ap.add_argument(
        "--env-json",
        default=None,
        help="Runtime env json path containing total_vram_bytes (and optionally gpu_name).",
    )
    ap.add_argument(
        "--allow-gpu-mismatch",
        action="store_true",
        help="Proceed on runtime/calibration mismatch with an explicit warning.",
    )

    ns = ap.parse_args(argv)
    try:
        model = gpu_capacity_model.load_capacity_model(ns.model)
        runtime_gpu_name: Optional[str] = None
        runtime_total_vram: Optional[int] = None if ns.total_vram_bytes is None else int(ns.total_vram_bytes)
        if ns.env_json:
            runtime_ctx = gpu_capacity_model.load_runtime_context_from_env_json(ns.env_json)
            runtime_gpu_name = runtime_ctx.gpu_name
            if runtime_total_vram is None:
                runtime_total_vram = int(runtime_ctx.total_vram_bytes)
        if runtime_total_vram is None:
            raise gpu_capacity_model.CapacityModelError(
                "runtime VRAM is required: pass --total-vram-bytes or --env-json"
            )

        issues = gpu_capacity_model.runtime_compatibility_issues(
            model,
            runtime_total_vram_bytes=runtime_total_vram,
            runtime_gpu_name=runtime_gpu_name,
        )
        if issues and not ns.allow_gpu_mismatch:
            raise gpu_capacity_model.CapacityModelError(
                "calibration/runtime mismatch: "
                + "; ".join(issues)
                + ". Re-run with --allow-gpu-mismatch only if this is intentional."
            )
        if issues and ns.allow_gpu_mismatch:
            print("WARNING: calibration/runtime mismatch accepted via --allow-gpu-mismatch:", file=sys.stderr)
            for issue in issues:
                print(f"WARNING: {issue}", file=sys.stderr)

        _, combo_key = gpu_capacity_model.compute_combo_key_from_workload_files(
            ns.ant,
            ns.colony,
            precision_override=model.track.precision,
        )
        guard_ratio = float(model.guard_ratio if ns.guard_ratio is None else ns.guard_ratio)
        max_b = model.estimate_max_batch(combo_key, guard_ratio=guard_ratio, total_vram_bytes=runtime_total_vram)
        safe_b = model.estimate_safe_start_batch(combo_key, total_vram_bytes=runtime_total_vram)
        print(f"SAFE_START={safe_b}")
        print(f"MAX={max_b}")
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

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
        help="Override total VRAM bytes (default: model.calibrated_on.total_vram_bytes).",
    )

    ns = ap.parse_args(argv)
    try:
        safe_b, max_b = gpu_capacity_model.estimate_safe_start_and_max(
            ant_path=ns.ant,
            colony_path=ns.colony,
            model_path=ns.model,
            guard_ratio=ns.guard_ratio,
            total_vram_bytes=ns.total_vram_bytes,
        )
        print(f"SAFE_START={safe_b}")
        print(f"MAX={max_b}")
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

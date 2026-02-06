"""VRA-35: fit OD1 capacity model v1 from probe run folders.

Reads probe artifacts under a gitignored runs-root and emits a committed,
public-safe calibration JSON file (no secrets, no absolute paths).
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

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


from tools.gpu_capacity_model import GUARD_BASIS_RESERVED, SCHEMA_VERSION, compute_combo_key


class FitError(RuntimeError):
    pass


def _stable_json_dump(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _rel_repo_path(path: Path) -> str:
    # Runs-root is already under the repo; keep output repo-relative and forward-slash.
    try:
        repo_root = Path(__file__).resolve().parents[2]
        rel = path.resolve().relative_to(repo_root.resolve())
        return rel.as_posix()
    except Exception:
        return path.as_posix()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class RunRecord:
    run_dir: Path
    ant_path: Optional[str]
    colony_path: Optional[str]
    canonical_spec: dict[str, Any]
    precision: str
    amp: int
    out_dim: int
    measure_steps: int
    batch: int
    alloc: Optional[int]
    reserved: Optional[int]
    stability_pass: bool
    had_oom: bool
    had_nan: bool
    had_inf: bool
    fail_reasons: list[str]
    total_vram_bytes: int
    gpu_name: str
    driver_version: Optional[str]
    torch_version: Optional[str]
    os_name: Optional[str]

    @property
    def is_pass(self) -> bool:
        return bool(self.stability_pass and (not self.had_oom) and (not self.had_nan) and (not self.had_inf))

    @property
    def overhead_bytes(self) -> Optional[int]:
        if self.alloc is None or self.reserved is None:
            return None
        return int(self.reserved) - int(self.alloc)


def _parse_run_cmd_argv(argv: list[str]) -> tuple[Optional[str], Optional[str]]:
    ant: Optional[str] = None
    colony: Optional[str] = None
    for idx, tok in enumerate(argv):
        if tok == "--ant" and idx + 1 < len(argv):
            ant = argv[idx + 1]
        if tok == "--colony" and idx + 1 < len(argv):
            colony = argv[idx + 1]
    return ant, colony


def try_load_run_record(run_dir: Path) -> Optional[RunRecord]:
    run_cmd = run_dir / "run_cmd.txt"
    metrics = run_dir / "metrics.json"
    env = run_dir / "env.json"

    if not (run_cmd.exists() and env.exists() and metrics.exists()):
        return None

    runcmd = _load_json(run_cmd)
    argv = runcmd.get("argv") or []
    ant_path, colony_path = _parse_run_cmd_argv(argv) if isinstance(argv, list) else (None, None)
    canonical_spec = runcmd.get("canonical_spec")
    if not isinstance(canonical_spec, dict):
        return None

    met = _load_json(metrics)
    ev = _load_json(env)

    try:
        return RunRecord(
            run_dir=run_dir,
            ant_path=ant_path,
            colony_path=colony_path,
            canonical_spec=canonical_spec,
            precision=str(met.get("precision")),
            amp=int(met.get("amp")),
            out_dim=int(met.get("out_dim")),
            measure_steps=int(met.get("measure_steps")),
            batch=int(met.get("batch_size")),
            alloc=None if met.get("peak_vram_allocated_bytes") is None else int(met.get("peak_vram_allocated_bytes")),
            reserved=None if met.get("peak_vram_reserved_bytes") is None else int(met.get("peak_vram_reserved_bytes")),
            stability_pass=bool(met.get("stability_pass")),
            had_oom=bool(met.get("had_oom")),
            had_nan=bool(met.get("had_nan")),
            had_inf=bool(met.get("had_inf")),
            fail_reasons=list(met.get("fail_reasons") or []),
            total_vram_bytes=int(ev.get("total_vram_bytes")),
            gpu_name=str(ev.get("gpu_name")),
            driver_version=ev.get("driver_version"),
            torch_version=ev.get("torch_version"),
            os_name=ev.get("os"),
        )
    except Exception:
        return None


def combo_spec_no_batch_from_canonical_spec(canonical_spec: dict[str, Any]) -> dict[str, Any]:
    if canonical_spec.get("schema_version") != "workload_schema_v1":
        raise FitError("unexpected schema_version in canonical_spec")
    ant_spec = canonical_spec.get("ant_spec")
    colony_spec = canonical_spec.get("colony_spec")
    if not isinstance(ant_spec, dict) or not isinstance(colony_spec, dict):
        raise FitError("canonical_spec missing ant_spec/colony_spec")
    return {
        "schema_version": "workload_schema_v1",
        "ant_spec": ant_spec,
        "colony_spec": {k: v for k, v in colony_spec.items() if k != "batch_size"},
    }


def _infer_combo_name(ant_path: Optional[str], colony_path: Optional[str]) -> str:
    if ant_path and colony_path and ant_path.endswith(".json") and colony_path.endswith(".json"):
        a = Path(ant_path).stem.replace("od1_", "").replace("_v1", "")
        c = Path(colony_path).stem.replace("od1_", "").replace("_v1", "")
        if a == "small" and c == "real":
            return "C1_smallxreal"
        if a == "real" and c == "real":
            return "C2_realxreal"
        if a == "stress" and c == "real":
            return "C3_stressxreal"
        if a == "real" and c == "small":
            return "C4_realxsmall"
        return f"{a}x{c}"
    return "unknown_combo"


def fit_capacity_model_v1(
    *,
    runs_root: Path,
    guard_ratio: float,
    safe_start_ratio: float,
    guard_basis: str,
    measure_steps: Optional[int],
) -> dict[str, Any]:
    if guard_basis != GUARD_BASIS_RESERVED:
        raise FitError("v1 supports guard_basis=reserved only")

    run_dirs = sorted([p for p in runs_root.iterdir() if p.is_dir()], key=lambda p: p.name)
    recs = [r for p in run_dirs if (r := try_load_run_record(p)) is not None]
    if not recs:
        raise FitError("no complete runs found (expected run_cmd.txt + metrics.json + env.json)")

    pass_recs = [r for r in recs if r.is_pass]
    if not pass_recs:
        raise FitError("no PASS runs found")

    if measure_steps is None:
        measure_steps = max(int(r.measure_steps) for r in pass_recs)

    recs = [r for r in recs if int(r.measure_steps) == int(measure_steps)]
    pass_recs = [r for r in recs if r.is_pass]
    if not pass_recs:
        raise FitError(f"no PASS runs found at measure_steps={measure_steps}")

    prec = {r.precision for r in pass_recs}
    amps = {int(r.amp) for r in pass_recs}
    outs = {int(r.out_dim) for r in pass_recs}
    if len(prec) != 1 or len(amps) != 1 or len(outs) != 1:
        raise FitError("PASS runs have inconsistent (precision, amp, out_dim); filter your runs-root")

    track = {"out_dim": int(next(iter(outs))), "precision": next(iter(prec)), "amp": int(next(iter(amps)))}
    if int(track["out_dim"]) != 1:
        raise FitError("capacity model v1 is OD1 only (out_dim=1)")

    overheads = [r.overhead_bytes for r in pass_recs if r.overhead_bytes is not None]
    if not overheads:
        raise FitError("cannot compute overhead median (missing alloc/reserved in PASS runs)")
    overhead_bytes = int(round(float(statistics.median(overheads))))

    tv = {int(r.total_vram_bytes) for r in pass_recs}
    if len(tv) != 1:
        raise FitError("PASS runs disagree on total_vram_bytes; refusing to fit")
    exemplar = sorted(pass_recs, key=lambda r: (r.gpu_name, r.batch, r.run_dir.name))[0]
    calibrated_on = {
        "gpu_name": exemplar.gpu_name,
        "total_vram_bytes": int(exemplar.total_vram_bytes),
        "driver_version": exemplar.driver_version,
        "torch_version": exemplar.torch_version,
        "os": exemplar.os_name,
    }

    by_combo: dict[str, list[RunRecord]] = {}
    combo_meta: dict[str, dict[str, Any]] = {}
    for r in recs:
        spec_nb = combo_spec_no_batch_from_canonical_spec(r.canonical_spec)
        ck = compute_combo_key(spec_nb)
        by_combo.setdefault(ck, []).append(r)
        if ck not in combo_meta:
            combo_meta[ck] = {
                "combo_spec_no_batch": spec_nb,
                "combo_name": _infer_combo_name(r.ant_path, r.colony_path),
                "ant_path": r.ant_path,
                "colony_path": r.colony_path,
            }

    combos_out: list[dict[str, Any]] = []
    for ck in sorted(by_combo.keys(), key=lambda k: combo_meta[k]["combo_name"]):
        runs = by_combo[ck]
        pass_runs = sorted([r for r in runs if r.is_pass], key=lambda r: (r.batch, r.run_dir.name))
        if not pass_runs:
            continue

        measured_max = max(int(r.batch) for r in pass_runs)
        fail_above = sorted(
            [r for r in runs if (not r.is_pass) and int(r.batch) > int(measured_max)],
            key=lambda r: (r.batch, r.run_dir.name),
        )
        boundary_fail = fail_above[0] if fail_above else None

        fit_points: list[RunRecord] = []
        if pass_runs:
            fit_points.append(pass_runs[0])
            for r in pass_runs[1:]:
                if int(r.batch) != int(fit_points[0].batch):
                    fit_points.append(r)
                    break

        base_alloc: Optional[int] = None
        per_batch: Optional[int] = None
        if len(fit_points) >= 2 and fit_points[0].alloc is not None and fit_points[1].alloc is not None:
            r1, r2 = fit_points[0], fit_points[1]
            db = int(r2.batch) - int(r1.batch)
            if db <= 0:
                raise FitError("invalid fit batch ordering")
            per = (int(r2.alloc) - int(r1.alloc)) / float(db)
            per_batch = int(round(per))
            base_alloc = int(round(int(r1.alloc) - per_batch * int(r1.batch)))

        combos_out.append(
            {
                "combo_name": combo_meta[ck]["combo_name"],
                "combo_key": ck,
                "ant_path": combo_meta[ck]["ant_path"],
                "colony_path": combo_meta[ck]["colony_path"],
                "combo_spec_no_batch": combo_meta[ck]["combo_spec_no_batch"],
                "base_alloc_bytes": base_alloc,
                "per_batch_alloc_bytes": per_batch,
                "measured_max_batch": int(measured_max),
                "boundary_fail_batch": None if boundary_fail is None else int(boundary_fail.batch),
                "boundary_fail_reasons": None if boundary_fail is None else list(boundary_fail.fail_reasons),
                "fit_points": [
                    {
                        "batch": int(r.batch),
                        "alloc": r.alloc,
                        "reserved": r.reserved,
                        "run_dir": _rel_repo_path(r.run_dir),
                    }
                    for r in fit_points
                    if r.alloc is not None and r.reserved is not None
                ],
                "pass_runs": [
                    {
                        "batch": int(r.batch),
                        "alloc": r.alloc,
                        "reserved": r.reserved,
                        "run_dir": _rel_repo_path(r.run_dir),
                    }
                    for r in pass_runs
                    if r.alloc is not None and r.reserved is not None
                ],
            }
        )

    if not combos_out:
        raise FitError("no combos emitted (did all runs fail parsing?)")

    combos_out = sorted(combos_out, key=lambda c: str(c["combo_name"]))

    return {
        "schema_version": SCHEMA_VERSION,
        "guard_basis": guard_basis,
        "guard_ratio": float(guard_ratio),
        "safe_start_ratio": float(safe_start_ratio),
        "track": track,
        "calibrated_on": calibrated_on,
        "overhead_bytes": int(overhead_bytes),
        "measure_steps": int(measure_steps),
        "runs_root": _rel_repo_path(runs_root),
        "combos": combos_out,
        "notes": "OD1 only (out_dim=1). Do not reuse on different GPUs without refit. Probe harness unchanged.",
    }


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Fit VRA-35 capacity_model_v1.json from probe run folders.")
    ap.add_argument("--runs-root", required=True, help="Root folder containing probe run directories.")
    ap.add_argument("--out", required=True, help="Output JSON path (e.g. Golden Draft/tools/capacity_model_v1.json).")
    ap.add_argument("--guard-basis", default=GUARD_BASIS_RESERVED, help="Guard basis (v1 supports reserved only).")
    ap.add_argument("--guard-ratio", type=float, default=0.92, help="VRAM guard ratio (reserved).")
    ap.add_argument("--safe-start-ratio", type=float, default=0.85, help="Conservative SAFE_START ratio.")
    ap.add_argument("--measure-steps", type=int, default=None, help="Filter to this measure_steps (default: max PASS).")

    ns = ap.parse_args(argv)
    try:
        model = fit_capacity_model_v1(
            runs_root=Path(ns.runs_root),
            guard_ratio=float(ns.guard_ratio),
            safe_start_ratio=float(ns.safe_start_ratio),
            guard_basis=str(ns.guard_basis),
            measure_steps=ns.measure_steps,
        )
        _stable_json_dump(Path(ns.out), model)
        return 0
    except FitError as exc:
        print(f"fit error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

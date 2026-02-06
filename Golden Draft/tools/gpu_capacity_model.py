"""VRA-35: OD1 capacity model (SAFE_START + MAX batch) from calibration JSON.

Guardrails (v1):
- Does NOT modify the probe harness.
- Does NOT hardcode calibration constants in code.
- OD1 only: out_dim must be 1.
- Guard basis: reserved bytes (peak_vram_reserved_bytes) only.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional


SCHEMA_VERSION = "capacity_model_v1"
GUARD_BASIS_RESERVED = "reserved"


class CapacityModelError(RuntimeError):
    pass


def _stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha12_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:12]


def compute_combo_key(combo_spec_no_batch: Mapping[str, Any]) -> str:
    """Compute a stable key for a (ant_spec, colony_spec-without-batch) spec."""

    return f"combo_v1_{_sha12_hex(_stable_json(combo_spec_no_batch))}"


def _req(obj: Mapping[str, Any], key: str) -> Any:
    if key not in obj:
        raise CapacityModelError(f"missing required key: {key}")
    return obj[key]


def _as_int(name: str, val: Any) -> int:
    if isinstance(val, bool) or not isinstance(val, (int, float)) or math.isnan(float(val)):
        raise CapacityModelError(f"{name} must be a number, got {type(val).__name__}")
    return int(val)


def _as_float(name: str, val: Any) -> float:
    if isinstance(val, bool) or not isinstance(val, (int, float)) or math.isnan(float(val)):
        raise CapacityModelError(f"{name} must be a number, got {type(val).__name__}")
    return float(val)


@dataclass(frozen=True)
class CapacityTrack:
    out_dim: int
    precision: str
    amp: int


@dataclass(frozen=True)
class CapacityCombo:
    combo_name: str
    combo_key: str
    combo_spec_no_batch: Mapping[str, Any]
    base_alloc_bytes: Optional[int]
    per_batch_alloc_bytes: Optional[int]
    measured_max_batch: Optional[int]


@dataclass(frozen=True)
class CapacityModelV1:
    guard_basis: str
    guard_ratio: float
    safe_start_ratio: float
    track: CapacityTrack
    calibrated_on: Mapping[str, Any]
    overhead_bytes: int
    combos_by_key: Mapping[str, CapacityCombo]

    def assert_track_compatible(self, *, out_dim: int) -> None:
        if int(out_dim) != int(self.track.out_dim):
            raise CapacityModelError(f"out_dim={out_dim} unsupported by model (expects {self.track.out_dim})")
        if int(out_dim) != 1:
            raise CapacityModelError("capacity model v1 supports out_dim=1 only")

    def _estimate_from_combo(
        self,
        combo: CapacityCombo,
        *,
        guard_ratio: float,
        total_vram_bytes: int,
        capacity_bytes: int,
    ) -> int:
        if combo.per_batch_alloc_bytes is None or combo.base_alloc_bytes is None:
            if combo.measured_max_batch is not None:
                return int(combo.measured_max_batch)
            raise CapacityModelError(
                f"combo {combo.combo_name} has no slope/intercept and no measured_max_batch; cannot estimate"
            )

        per_batch = int(combo.per_batch_alloc_bytes)
        base = int(combo.base_alloc_bytes)
        if per_batch <= 0:
            raise CapacityModelError(f"combo {combo.combo_name} has invalid per_batch_alloc_bytes={per_batch}")

        numer = capacity_bytes - int(self.overhead_bytes) - base
        if numer <= 0:
            return 1

        bmax = int(math.floor(numer / per_batch))
        bmax = max(1, bmax)

        if total_vram_bytes > 0 and bmax > 1_000_000:
            raise CapacityModelError(f"unreasonable MAX batch computed: {bmax}")
        return bmax

    def estimate_max_batch(
        self,
        combo_key: str,
        *,
        guard_ratio: float,
        total_vram_bytes: Optional[int] = None,
    ) -> int:
        if self.guard_basis != GUARD_BASIS_RESERVED:
            raise CapacityModelError(f"unsupported guard_basis={self.guard_basis} (v1 expects reserved)")

        combo = self.combos_by_key.get(combo_key)
        if combo is None:
            raise CapacityModelError(f"no calibration found for combo_key={combo_key}")

        tvb = int(total_vram_bytes) if total_vram_bytes is not None else _as_int(
            "calibrated_on.total_vram_bytes", _req(self.calibrated_on, "total_vram_bytes")
        )
        cap = int(math.floor(float(guard_ratio) * tvb))
        return self._estimate_from_combo(combo, guard_ratio=float(guard_ratio), total_vram_bytes=tvb, capacity_bytes=cap)

    def estimate_safe_start_batch(
        self,
        combo_key: str,
        *,
        total_vram_bytes: Optional[int] = None,
    ) -> int:
        tvb = int(total_vram_bytes) if total_vram_bytes is not None else _as_int(
            "calibrated_on.total_vram_bytes", _req(self.calibrated_on, "total_vram_bytes")
        )
        cap = int(math.floor(float(self.safe_start_ratio) * tvb))
        max_b = self.estimate_max_batch(combo_key, guard_ratio=self.guard_ratio, total_vram_bytes=tvb)
        safe_b = self._estimate_from_combo(
            _req(self.combos_by_key, combo_key),
            guard_ratio=self.safe_start_ratio,
            total_vram_bytes=tvb,
            capacity_bytes=cap,
        )
        return max(1, min(int(safe_b), int(max_b)))


def load_capacity_model(path: str | Path) -> CapacityModelV1:
    pth = Path(path)
    data = json.loads(pth.read_text(encoding="utf-8"))
    if _req(data, "schema_version") != SCHEMA_VERSION:
        raise CapacityModelError("unsupported schema_version")

    guard_basis = str(_req(data, "guard_basis"))
    guard_ratio = _as_float("guard_ratio", _req(data, "guard_ratio"))
    safe_ratio = _as_float("safe_start_ratio", _req(data, "safe_start_ratio"))

    track_obj = _req(data, "track")
    track = CapacityTrack(
        out_dim=_as_int("track.out_dim", _req(track_obj, "out_dim")),
        precision=str(_req(track_obj, "precision")),
        amp=_as_int("track.amp", _req(track_obj, "amp")),
    )

    overhead = _as_int("overhead_bytes", _req(data, "overhead_bytes"))
    calibrated_on = _req(data, "calibrated_on")
    if not isinstance(calibrated_on, dict):
        raise CapacityModelError("calibrated_on must be an object")

    combos_obj = _req(data, "combos")
    if not isinstance(combos_obj, list):
        raise CapacityModelError("combos must be a list")

    combos: dict[str, CapacityCombo] = {}
    for idx, c in enumerate(combos_obj):
        if not isinstance(c, dict):
            raise CapacityModelError(f"combos[{idx}] must be an object")
        key = str(_req(c, "combo_key"))
        if key in combos:
            raise CapacityModelError(f"duplicate combo_key in model: {key}")
        base = c.get("base_alloc_bytes")
        perb = c.get("per_batch_alloc_bytes")
        measured_max = c.get("measured_max_batch")
        combos[key] = CapacityCombo(
            combo_name=str(_req(c, "combo_name")),
            combo_key=key,
            combo_spec_no_batch=_req(c, "combo_spec_no_batch"),
            base_alloc_bytes=None if base is None else _as_int("base_alloc_bytes", base),
            per_batch_alloc_bytes=None if perb is None else _as_int("per_batch_alloc_bytes", perb),
            measured_max_batch=None if measured_max is None else _as_int("measured_max_batch", measured_max),
        )

    return CapacityModelV1(
        guard_basis=guard_basis,
        guard_ratio=float(guard_ratio),
        safe_start_ratio=float(safe_ratio),
        track=track,
        calibrated_on=calibrated_on,
        overhead_bytes=int(overhead),
        combos_by_key=combos,
    )


def compute_combo_key_from_workload_files(
    ant_path: str | Path,
    colony_path: str | Path,
    *,
    precision_override: Optional[str] = None,
) -> tuple[dict[str, Any], str]:
    """Compute the capacity combo key for (ant_spec from ant_path, colony_spec from colony_path)."""

    from tools import workload_id

    ant = workload_id.load_workload_spec(str(ant_path))
    col = workload_id.load_workload_spec(str(colony_path))
    ant_canon = workload_id.canonicalize_spec(ant)
    col_canon = workload_id.canonicalize_spec(col)

    schema_version = str(_req(ant_canon, "schema_version"))
    if str(_req(col_canon, "schema_version")) != schema_version:
        raise CapacityModelError("schema_version mismatch between ant and colony specs")

    combo_spec_no_batch: dict[str, Any] = {
        "schema_version": schema_version,
        "ant_spec": _req(ant_canon, "ant_spec"),
        "colony_spec": {k: v for k, v in _req(col_canon, "colony_spec").items() if k != "batch_size"},
    }
    if precision_override is not None:
        combo_spec_no_batch["ant_spec"] = dict(combo_spec_no_batch["ant_spec"])
        combo_spec_no_batch["ant_spec"]["precision"] = str(precision_override)
    return combo_spec_no_batch, compute_combo_key(combo_spec_no_batch)


def estimate_safe_start_and_max(
    *,
    ant_path: str | Path,
    colony_path: str | Path,
    model_path: str | Path,
    guard_ratio: Optional[float] = None,
    total_vram_bytes: Optional[int] = None,
) -> tuple[int, int]:
    model = load_capacity_model(model_path)
    model.assert_track_compatible(out_dim=model.track.out_dim)

    _, combo_key = compute_combo_key_from_workload_files(
        ant_path,
        colony_path,
        precision_override=model.track.precision,
    )
    gr = float(model.guard_ratio if guard_ratio is None else guard_ratio)
    max_b = model.estimate_max_batch(combo_key, guard_ratio=gr, total_vram_bytes=total_vram_bytes)
    safe_b = model.estimate_safe_start_batch(combo_key, total_vram_bytes=total_vram_bytes)
    return safe_b, max_b

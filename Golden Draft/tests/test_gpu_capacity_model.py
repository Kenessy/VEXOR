"""VRA-35 tests: gpu_capacity_model estimators (CPU-only)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import conftest  # noqa: F401  (import side-effect: sys.path bootstrap)

from tools import gpu_capacity_model


class TestGpuCapacityModel(unittest.TestCase):
    def test_max_safe_monotonic_and_out_dim_guard(self) -> None:
        model = {
            "schema_version": "capacity_model_v1",
            "guard_basis": "reserved",
            "guard_ratio": 0.92,
            "safe_start_ratio": 0.85,
            "track": {"out_dim": 1, "precision": "fp16", "amp": 1},
            "calibrated_on": {"gpu_name": "TEST_GPU", "total_vram_bytes": 1000},
            "overhead_bytes": 5,
            "combos": [
                {
                    "combo_name": "C2_realxreal",
                    "combo_key": "combo_v1_deadbeefcafe",
                    "combo_spec_no_batch": {},
                    "base_alloc_bytes": 100,
                    "per_batch_alloc_bytes": 10,
                    "measured_max_batch": None,
                }
            ],
        }

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "m.json"
            p.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            m = gpu_capacity_model.load_capacity_model(p)
            m.assert_track_compatible(out_dim=1)

            max90 = m.estimate_max_batch("combo_v1_deadbeefcafe", guard_ratio=0.90, total_vram_bytes=1000)
            max92 = m.estimate_max_batch("combo_v1_deadbeefcafe", guard_ratio=0.92, total_vram_bytes=1000)
            self.assertGreaterEqual(max92, max90)

            safe = m.estimate_safe_start_batch("combo_v1_deadbeefcafe", total_vram_bytes=1000)
            self.assertLessEqual(safe, max92)

            with self.assertRaises(gpu_capacity_model.CapacityModelError):
                m.assert_track_compatible(out_dim=2)


"""VRA-35 pass-2 tests: strict runtime portability for gpu_capacity_pick_batch CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import conftest  # noqa: F401  (import side-effect: sys.path bootstrap)

from tools import gpu_capacity_model


class TestGpuCapacityPickBatchCli(unittest.TestCase):
    def test_strict_requires_runtime_vram_and_override_warns(self) -> None:
        ant_spec = {
            "schema_version": "workload_schema_v1",
            "ant_spec": {"ring_len": 32, "slot_dim": 16, "ptr_dtype": "fp64", "precision": "fp32"},
            "colony_spec": {
                "seq_len": 8,
                "synth_len": 8,
                "batch_size": 4,
                "ptr_update_every": 1,
                "state_loop_samples": 0,
            },
        }
        colony_spec = {
            "schema_version": "workload_schema_v1",
            "ant_spec": {"ring_len": 64, "slot_dim": 32, "ptr_dtype": "fp64", "precision": "fp32"},
            "colony_spec": {
                "seq_len": 8,
                "synth_len": 8,
                "batch_size": 16,
                "ptr_update_every": 1,
                "state_loop_samples": 0,
            },
        }

        script = Path(__file__).resolve().parents[1] / "tools" / "gpu_capacity_pick_batch.py"
        repo_root = Path(__file__).resolve().parents[2]

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            ant_path = tmp / "ant.json"
            colony_path = tmp / "colony.json"
            ant_path.write_text(json.dumps(ant_spec, indent=2) + "\n", encoding="utf-8")
            colony_path.write_text(json.dumps(colony_spec, indent=2) + "\n", encoding="utf-8")

            _, combo_key = gpu_capacity_model.compute_combo_key_from_workload_files(
                ant_path, colony_path, precision_override="fp16"
            )
            model = {
                "schema_version": "capacity_model_v1",
                "guard_basis": "reserved",
                "guard_ratio": 0.92,
                "safe_start_ratio": 0.85,
                "track": {"out_dim": 1, "precision": "fp16", "amp": 1},
                "calibrated_on": {"gpu_name": "GPU_A", "total_vram_bytes": 1000},
                "overhead_bytes": 5,
                "combos": [
                    {
                        "combo_name": "CX",
                        "combo_key": combo_key,
                        "combo_spec_no_batch": {},
                        "base_alloc_bytes": 100,
                        "per_batch_alloc_bytes": 10,
                        "measured_max_batch": None,
                    }
                ],
            }
            model_path = tmp / "model.json"
            model_path.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            def _run(extra: list[str]) -> subprocess.CompletedProcess[str]:
                cmd = [
                    sys.executable,
                    str(script),
                    "--ant",
                    str(ant_path),
                    "--colony",
                    str(colony_path),
                    "--model",
                    str(model_path),
                    *extra,
                ]
                return subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True, timeout=20)

            missing_runtime = _run([])
            self.assertEqual(missing_runtime.returncode, 2)
            self.assertIn("runtime VRAM is required", missing_runtime.stderr)

            strict_mismatch = _run(["--total-vram-bytes", "900"])
            self.assertEqual(strict_mismatch.returncode, 2)
            self.assertIn("calibration/runtime mismatch", strict_mismatch.stderr)

            allowed_mismatch = _run(["--total-vram-bytes", "900", "--allow-gpu-mismatch"])
            self.assertEqual(allowed_mismatch.returncode, 0)
            self.assertIn("SAFE_START=", allowed_mismatch.stdout)
            self.assertIn("MAX=", allowed_mismatch.stdout)
            self.assertIn("WARNING: calibration/runtime mismatch", allowed_mismatch.stderr)

            strict_match = _run(["--total-vram-bytes", "1000"])
            self.assertEqual(strict_match.returncode, 0)
            self.assertIn("SAFE_START=", strict_match.stdout)
            self.assertIn("MAX=", strict_match.stdout)


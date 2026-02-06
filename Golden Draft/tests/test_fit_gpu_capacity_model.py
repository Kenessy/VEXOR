"""VRA-35 tests: fit_gpu_capacity_model (CPU-only)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import conftest  # noqa: F401  (import side-effect: sys.path bootstrap)

from tools import fit_gpu_capacity_model


def _write_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _mk_run(
    root: Path,
    name: str,
    *,
    ant_path: str,
    colony_path: str,
    batch: int,
    alloc: int,
    reserved: int,
    stability_pass: bool,
    fail_reasons: list[str] | None = None,
    measure_steps: int = 50,
    precision: str = "fp16",
    amp: int = 1,
    out_dim: int = 1,
    total_vram_bytes: int = 1000,
) -> None:
    run_dir = root / name
    run_dir.mkdir(parents=True, exist_ok=True)

    run_cmd = {
        "argv": [
            "Golden Draft\\tools\\gpu_capacity_probe.py",
            "--ant",
            ant_path,
            "--colony",
            colony_path,
            "--out-dim",
            str(out_dim),
            "--batch",
            str(batch),
            "--measure-steps",
            str(measure_steps),
        ],
        "canonical_spec": {
            "schema_version": "workload_schema_v1",
            "ant_spec": {"ring_len": 32, "slot_dim": 16, "ptr_dtype": "fp64", "precision": precision},
            "colony_spec": {
                "seq_len": 8,
                "synth_len": 8,
                "batch_size": batch,
                "ptr_update_every": 1,
                "state_loop_samples": 0,
            },
        },
    }
    _write_json(run_dir / "run_cmd.txt", run_cmd)

    metrics = {
        "batch_size": batch,
        "precision": precision,
        "amp": amp,
        "out_dim": out_dim,
        "measure_steps": measure_steps,
        "peak_vram_allocated_bytes": alloc,
        "peak_vram_reserved_bytes": reserved,
        "stability_pass": stability_pass,
        "had_oom": False,
        "had_nan": False,
        "had_inf": False,
        "fail_reasons": fail_reasons or ([] if stability_pass else ["vram_guard"]),
    }
    _write_json(run_dir / "metrics.json", metrics)

    env = {
        "total_vram_bytes": total_vram_bytes,
        "gpu_name": "TEST_GPU",
        "driver_version": "x",
        "torch_version": "y",
        "os": "test",
    }
    _write_json(run_dir / "env.json", env)


class TestFitGpuCapacityModel(unittest.TestCase):
    def test_deterministic_fit_and_skips_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "runs"
            root.mkdir(parents=True, exist_ok=True)

            _mk_run(
                root,
                "c2_realxreal_B01_ms50",
                ant_path="Golden Draft\\workloads\\od1_real_v1.json",
                colony_path="Golden Draft\\workloads\\od1_real_v1.json",
                batch=1,
                alloc=100,
                reserved=120,
                stability_pass=True,
            )
            _mk_run(
                root,
                "c2_realxreal_B02_ms50",
                ant_path="Golden Draft\\workloads\\od1_real_v1.json",
                colony_path="Golden Draft\\workloads\\od1_real_v1.json",
                batch=2,
                alloc=130,
                reserved=155,
                stability_pass=True,
            )
            _mk_run(
                root,
                "c2_realxreal_B03_ms50_fail",
                ant_path="Golden Draft\\workloads\\od1_real_v1.json",
                colony_path="Golden Draft\\workloads\\od1_real_v1.json",
                batch=3,
                alloc=160,
                reserved=950,
                stability_pass=False,
                fail_reasons=["vram_guard"],
            )
            # Incomplete run (should be ignored).
            (root / "incomplete").mkdir()
            (root / "incomplete" / "run_cmd.txt").write_text("{}", encoding="utf-8")

            model1 = fit_gpu_capacity_model.fit_capacity_model_v1(
                runs_root=root,
                guard_ratio=0.92,
                safe_start_ratio=0.85,
                guard_basis="reserved",
                measure_steps=50,
            )
            model2 = fit_gpu_capacity_model.fit_capacity_model_v1(
                runs_root=root,
                guard_ratio=0.92,
                safe_start_ratio=0.85,
                guard_basis="reserved",
                measure_steps=50,
            )

            self.assertEqual(json.dumps(model1, sort_keys=True), json.dumps(model2, sort_keys=True))
            self.assertEqual(model1["schema_version"], "capacity_model_v1")
            self.assertEqual(model1["guard_basis"], "reserved")
            self.assertEqual(model1["track"]["out_dim"], 1)
            self.assertEqual(model1["track"]["precision"], "fp16")
            self.assertEqual(model1["track"]["amp"], 1)

            combos = model1["combos"]
            self.assertEqual(len(combos), 1)
            combo = combos[0]
            self.assertEqual(combo["combo_name"], "C2_realxreal")
            self.assertEqual(combo["measured_max_batch"], 2)
            self.assertEqual(combo["boundary_fail_batch"], 3)
            self.assertEqual(combo["base_alloc_bytes"], 70)  # 100 - 30*1
            self.assertEqual(combo["per_batch_alloc_bytes"], 30)


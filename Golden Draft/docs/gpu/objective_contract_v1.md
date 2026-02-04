# GPU Objective + Stability/Metrics Contract v1

Contract ID: `objective_contract_v1`
Path: `docs/gpu/objective_contract_v1.md`

This contract defines what a **valid GPU capacity/throughput run** is and the
minimum artifacts and metrics required to compare results. All GPU runs should
reference this contract in their run notes and/or harness `--help`.

---

## A) Purpose & Scope

- Applies to **GPU capacity / throughput characterization** runs for VRAXION.
- Defines:
  - the **primary objective metric** (rankable scalar),
  - **stability gates** (hard fail conditions),
  - **required artifacts** and schemas.

---

## B) Primary Objective (rankable metric)

**Primary scalar:** `throughput_samples_per_s`

**Definition:**
```
throughput_samples_per_s = (measure_steps * batch_size) / measure_wall_time_s
```

- Excludes warmup steps.
- Units: samples/second.

**Optional derived metric:** `throughput_tokens_per_s`
```
throughput_tokens_per_s = throughput_samples_per_s * seq_len
```

---

## B.1) Measurement protocol (required)

- **Warmup exclusion:** warmup steps are excluded from all timing statistics.
- **measure_wall_time_s:** wall-clock time covering only the **measure** window.
- **median_step_time_s / p95_step_time_s:** computed over per-step durations in the
  **measure** window only (exclude warmup).
- If a step is missing timing (e.g., crash), mark stability FAIL and record a reason.

---

## C) Stability Contract (hard fail gates)

A run **FAILS** if any of the following are true:

1) **OOM / CUDA errors** occurred.
2) **NaN/Inf** appears in tracked metrics.
3) **Step‑time explosion**:
   - `p95_step_time_s > 2.5 × median_step_time_s` (after warmup).
4) **Heartbeat stall**:
   - No step log for `max(60s, 10 × median_step_time_s)` after warmup.
5) **VRAM guard (default)**:
   - `peak_vram_reserved_bytes > 0.92 × total_vram_bytes`
   - Default guard ratio = **0.92** (allowed range 0.90–0.92 if explicitly noted).

---

## C.1) Windows / WDDM note (short)

- WDDM/TDR can kill long kernels or cause silent stalls.
- Prefer **shorter kernels**, smaller batches, or **Linux** for long runs.
- If WDDM is used, keep runs conservative and document any stalls explicitly.

---

## D) Required Artifacts + Schemas

Minimum artifact set (per run):

- `run_cmd.txt` — exact command invoked.
- `env.json` — hardware/software + git hash + precision.
- `metrics.json` — required metrics with units.
- `summary.md` — PASS/FAIL and reasons.
- `metrics.csv` — optional but allowed (if emitted, must match JSON keys).

### `env.json` (minimum keys)
```json
{
  "gpu_name": "RTX 4070 Ti 16GB",
  "total_vram_bytes": 17179869184,
  "driver_version": "xxx.xx",
  "cuda_version": "12.x",
  "torch_version": "2.x",
  "os": "Windows 11",
  "precision": "fp16",
  "amp": 1,
  "git_commit": "abcdef1"
}
```

### `metrics.json` (minimum keys)
```json
{
  "batch_size": 128,
  "seq_len": 128,
  "warmup_steps": 20,
  "measure_steps": 200,
  "measure_wall_time_s": 18.4,
  "median_step_time_s": 0.085,
  "p95_step_time_s": 0.19,
  "throughput_samples_per_s": 1391.3,
  "throughput_tokens_per_s": 178086.4,
  "peak_vram_reserved_bytes": 11223344556,
  "peak_vram_allocated_bytes": 9988776655,
  "had_oom": false,
  "had_nan": false,
  "had_inf": false,
  "stability_pass": true,
  "fail_reasons": []
}
```

---

## E) CLI Interface Contract (minimal)

The **probe harness `--help` must reference this contract**:
`docs/gpu/objective_contract_v1.md`

The full CLI implementation is **out of scope** for this contract and will be
implemented in VRA‑32.

---

## F) Evidence Rules (E2 vs E1)

- **E2 Check**: contract compliance + artifacts + reproducible metadata.
  - Must satisfy all stability gates and emit required files.
- **E1 Probe**: exploratory runs allowed, but **still must pass** stability gates.
  - Not necessarily rankable; only indicates feasibility.

---

## G) Acceptance Checklist (VRA‑30)

- `docs/gpu/objective_contract_v1.md` exists.
- Doc includes objective metric, stability gates, artifact schema, and examples.
- Probe harness `--help` references this contract path.
- Future GPU runs reference this contract (no random baselines).

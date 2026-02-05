# Contributing

VRAXION is a research repo where **mechanism + repeatability > vibes**.
If a change cannot be reproduced or audited, it is not done.

## Repo map

- `Golden Code/`: reusable runtime library code.
- `Golden Draft/`: tooling, tests, harnesses, and experiment-grade code.
- `docs/`: GitHub Pages site (public-facing).

## Where to put things

- Tools / harnesses / scripts: `Golden Draft/tools/`
- Unit tests (CPU-only by default): `Golden Draft/tests/`
- GPU measurement contracts and docs: `Golden Draft/docs/gpu/`
- Ops/process docs: `Golden Draft/docs/ops/`

## Branch naming

Use short, intent-revealing branch names. Examples:

- `feat/vra-32-gpu-probe-harness`
- `chore/ci-v1`
- `docs/audit-v1`

## Pull request requirements

Every PR should include:

- **Why**: what problem this solves.
- **What changed**: concise list of files/behavior changes.
- **How to verify**: exact commands.

And must respect these guardrails:

- Do not commit run artifacts (`bench_vault/`, `logs/`, checkpoints, large binaries).
- Keep PRs small and reversible; avoid mass refactors.
- If a change affects measurement/stability, verify against the contract:
  - `Golden Draft/docs/gpu/objective_contract_v1.md`

Recommended verification commands:

```powershell
python -m unittest discover -s "Golden Draft/tests" -v
python -m compileall "Golden Code" "Golden Draft"
```

## Issues, discussions, and internal tracking

- **GitHub Issues** in this repo are curated **public updates** (heartbeat/bundles), not the full internal tracker.
- For questions and design discussion, use **GitHub Discussions**.
- Internal execution planning and backlog live in Linear (not mirrored 1:1 here).

## Reproducibility

If you report a number (throughput, VRAM, stability), include a minimal result packet:

- commit hash
- `env.json`
- `workload_id`
- full CLI args and output directory

See: `Golden Draft/docs/ops/reproducibility_v1.md`

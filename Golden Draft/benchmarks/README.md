# VRAXION Benchmarks (Golden Draft)

This folder contains reproducible, longer-running benchmark/probe scripts.

Notes:
- These are NOT part of `unittest` discovery (they can take time / use GPU).
- All run artifacts should go under `bench_vault/` (git-ignored).
- Prefer append-only logs (`PYTHONUNBUFFERED=1`, unique filenames).

Current baseline "proof-of-boot" benchmark:
- `boot_synth_markov0/`: synthetic sequence classification using the existing
  INSTNCT pipeline (no external datasets).


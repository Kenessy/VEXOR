$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# CPU + fp64 baseline
$env:VAR_COMPUTE_DEVICE = "cpu"
$env:CUDA_VISIBLE_DEVICES = ""
$env:TP6_PRECISION = "fp64"
$env:TP6_PTR_DTYPE = "fp64"

# Threading
$env:OMP_NUM_THREADS = "24"
$env:MKL_NUM_THREADS = "24"

# Resume + checkpoints
$env:TP6_RESUME = "0"
$env:TP6_CKPT = "checkpoints/tier4_phase_a/checkpoint.pt"
$env:TP6_SAVE_EVERY_STEPS = "50"
$env:TP6_EVAL_EVERY_STEPS = "10"
$env:TP6_EVAL_AT_CHECKPOINT = "0"

# Synth config (assoc_mix baseline)
$env:TP6_SYNTH = "1"
$env:TP6_SYNTH_MODE = "assoc_mix"
$env:TP6_SYNTH_LEN = "64"
$env:TP6_ASSOC_KEYS = "2"
$env:TP6_ASSOC_VAL_RANGE = "2"
$env:TP6_ASSOC_PAIRS = "1"
$env:TP6_MAX_SAMPLES = "4096"
$env:TP6_BATCH_SIZE = "128"
$env:TP6_OFFLINE_ONLY = "1"

# Mix offsets + safe sentinel (key-only offset is applied in code)
$env:TP6_ASSOC_MIX_OFFSET = "100"
$env:TP6_ASSOC_MIX_CLEAN_OFFSET = "0"
$env:TP6_ASSOC_MIX_DOMAIN_TOKEN = "1"
$env:TP6_ASSOC_MIX_CLEAN_SENTINEL = "50"
$env:TP6_ASSOC_MIX_BYTE_SENTINEL = "150"

# Model config
$env:TP6_RING_LEN = "128"
$env:TP6_EXPERT_HEADS = "16"
$env:TP6_ANCHOR_CONF_MIN = "0.5"
$env:TP6_ANCHOR_MIN_STEP = "0.1"

# Biology disabled
$env:TP6_MITOSIS = "0"
$env:TP6_METABOLIC_HUNGER = "0"
$env:TP6_METABOLIC_TELEMETRY = "0"

# Runtime limit
$env:TP6_WALL = "240"
$env:TP6_IGNORE_WALL_CLOCK = "1"
$env:TP6_MAX_STEPS = "200"

# Logging
$env:VAR_LOGGING_PATH = "logs/tier4_phase_a_sentinel.log"

New-Item -ItemType Directory -Force -Path "checkpoints/tier4_phase_a" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null

Write-Host ">>> Tier4 Phase A (assoc_mix + safe sentinel) starting" -ForegroundColor Green
python tournament_phase6.py

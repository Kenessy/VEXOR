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
$env:TP6_CKPT = ""
$env:TP6_SAVE_EVERY_STEPS = "50"
$env:TP6_SAVE_EVERY = "50"
$env:TP6_EVAL_EVERY_STEPS = "10"
$env:TP6_EVAL_SAMPLES = "1024"
$env:TP6_EVAL_AT_CHECKPOINT = "1"

# Synth config (assoc_mix baseline)
$env:TP6_SYNTH = "1"
$env:TP6_SYNTH_MODE = "assoc_mix"
$env:TP6_SYNTH_LEN = "32"
$env:TP6_ASSOC_KEYS = "2"
$env:TP6_ASSOC_VAL_RANGE = "2"
$env:TP6_ASSOC_PAIRS = "1"
$env:TP6_MAX_SAMPLES = "4096"
$env:TP6_BATCH_SIZE = "128"
$env:TP6_OFFLINE_ONLY = "1"

# Mix offsets + safe sentinel (key-only offset is applied in code)
$env:TP6_ASSOC_MIX_CLEAN_OFFSET = "0"
$env:TP6_ASSOC_MIX_DOMAIN_TOKEN = "1"
$env:TP6_ASSOC_MIX_OFFSET = "10"
$env:TP6_ASSOC_MIX_CLEAN_SENTINEL = "5"
$env:TP6_ASSOC_MIX_BYTE_SENTINEL = "15"

# Model config
$env:TP6_RING_LEN = "128"
$env:TP6_EXPERT_HEADS = "18"
$env:TP6_ANCHOR_CONF_MIN = "0.3"
$env:TP6_ANCHOR_MIN_STEP = "0.05"
$env:TP6_UPDATE_SCALE = "0.05"
$env:TP6_LR = "0.01"

# Biology disabled for warmup
$env:TP6_MITOSIS = "0"
$env:TP6_METABOLIC_HUNGER = "0"
$env:TP6_METABOLIC_TELEMETRY = "0"

# Runtime limit (wall clock only for warmup)
$env:TP6_WALL = "600"
$env:TP6_IGNORE_WALL_CLOCK = "0"
$env:TP6_MAX_STEPS = "0"
$env:TP6_IGNORE_MAX_STEPS = "1"

# Logging
$env:VAR_LOGGING_PATH = "logs/tier4_phase_b_sentinel_warmup.log"

New-Item -ItemType Directory -Force -Path "checkpoints/tier4_phase_b_sentinel" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null

Write-Host ">>> Tier4 Phase B Warmup (assoc_mix + safe sentinel, biology off) starting" -ForegroundColor Green
Write-Host ">>> eval_every=$env:TP6_EVAL_EVERY_STEPS save_every=$env:TP6_SAVE_EVERY_STEPS/$env:TP6_SAVE_EVERY eval_samples=$env:TP6_EVAL_SAMPLES" -ForegroundColor DarkGray
python tournament_phase6.py

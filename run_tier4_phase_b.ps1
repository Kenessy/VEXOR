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
$env:TP6_RESUME = "1"
$env:TP6_CKPT = "checkpoints/mitosis/tier4_mix_mitosis_round3_split.pt"
$env:TP6_SAVE_EVERY_STEPS = "50"
$env:TP6_EVAL_EVERY_STEPS = "10"
$env:TP6_EVAL_AT_CHECKPOINT = "0"

# Synth config (assoc_mix baseline)
$env:TP6_SYNTH = "1"
$env:TP6_SYNTH_MODE = "assoc_mix"
$env:TP6_SYNTH_LEN = "64"
$env:TP6_ASSOC_KEYS = "8"
$env:TP6_ASSOC_VAL_RANGE = "4"
$env:TP6_ASSOC_PAIRS = "1"
$env:TP6_MAX_SAMPLES = "8192"
$env:TP6_BATCH_SIZE = "128"
$env:TP6_OFFLINE_ONLY = "1"

# Mix offsets (key-only offset is applied in code)
$env:TP6_ASSOC_MIX_OFFSET = "100"
$env:TP6_ASSOC_MIX_CLEAN_OFFSET = "0"
$env:TP6_ASSOC_MIX_DOMAIN_TOKEN = "0"

# Model config
$env:TP6_RING_LEN = "128"
$env:TP6_EXPERT_HEADS = "19"
$env:TP6_ANCHOR_CONF_MIN = "0.5"
$env:TP6_ANCHOR_MIN_STEP = "0.1"

# Biology
$env:TP6_MITOSIS = "1"
$env:TP6_MITOSIS_CKPT = "checkpoints/mitosis/tier4_mix_mitosis_round4.pt"
$env:TP6_MITOSIS_STALL_WINDOW = "30"
$env:TP6_MITOSIS_IMBALANCE = "0.1"
$env:TP6_MITOSIS_STALL_DELTA = "0.005"
$env:TP6_METABOLIC_HUNGER = "1"
$env:TP6_METABOLIC_TELEMETRY = "1"
$env:TP6_METABOLIC_COST_COEFF = "0.0001"
$env:TP6_METABOLIC_EVERY = "100"

# Runtime limit
$env:TP6_WALL = "600"
$env:TP6_IGNORE_WALL_CLOCK = "1"
$env:TP6_MAX_STEPS = "2000"

# Logging
$env:VAR_LOGGING_PATH = "logs/tier4_phase_b_round3_resume.log"

New-Item -ItemType Directory -Force -Path "checkpoints/tier4_phase_b" | Out-Null
New-Item -ItemType Directory -Force -Path "checkpoints/mitosis" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null

Write-Host ">>> Tier4 Phase B (assoc_mix + mitosis/hunger) starting" -ForegroundColor Green
python tournament_phase6.py

$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $here "run_boot_synth_markov0.py"

if (-not $env:PYTHONUNBUFFERED) { $env:PYTHONUNBUFFERED = "1" }

python -u $py @Args


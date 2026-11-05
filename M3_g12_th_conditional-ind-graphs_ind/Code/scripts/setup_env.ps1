# Rhino reproduction environment (Windows, PowerShell).
# This is the recipe that was actually run and imported successfully on the development PC (31 Oct 2026).
# Deviations from the repo's pyproject.toml are listed at the bottom.
param(
    [string]$EnvDir = "D:\rhino_env"   # keep this OUTSIDE OneDrive. Change if D: is not available.
)
$ErrorActionPreference = "Stop"

# 1. uv (fast installer that can also fetch Python 3.9). Skip if already present.
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}

# 2. Python 3.9 virtual environment (official code needs >=3.8,<3.10)
New-Item -ItemType Directory -Force $EnvDir | Out-Null
uv venv --python 3.9 "$EnvDir\venv"
$py = "$EnvDir\venv\Scripts\python.exe"

# 3. Core pinned packages. torch 1.12.1 is the CPU wheel on Windows (no CUDA build exists for it).
uv pip install --python $py "torch==1.12.1" "numpy<1.24" "pandas<1.6" "scipy<1.11" "scikit-learn<1.3" `
    "pytorch-lightning==1.7.7" "matplotlib<3.8" "seaborn<0.12" "networkx<2.9" tqdm "mlflow<1.31" gitpython `
    graphviz "igraph<0.10" "lingam==1.5.5" "dcor==0.5.3" "causal-learn<0.1.4" "tensorboard<2.12" `
    "setuptools<70" psutil

# 4. Packages that need special handling
uv pip install --python $py "numpyro==0.9.2" "pyro-ppl<1.9" "dowhy<0.10"
uv pip install --python $py --only-binary :all: "econml==0.14.1"     # econml 0.12 has no Windows py3.9 wheel
uv pip install --python $py "git+https://github.com/confoundry/trustworthyAI.git@a768c0a"   # gcastle, repo root
uv pip install --python $py "git+https://github.com/WenboGong/causalnex.git@develop"        # author fork
uv pip install --python $py "git+https://github.com/WenboGong/tigramite.git@develop"        # author fork

# 5. Smoke test
$env:PYTHONPATH = (Resolve-Path "$PSScriptRoot\..\causica").Path
& $py -c "import torch, causica.run_experiment; print('OK torch', torch.__version__)"

# Deviations from pyproject.toml:
#  - econml 0.14.1 instead of ^0.12.0 (no wheel for 0.12 on Windows). Only imported, not used by Rhino itself.
#  - jaxlib is not installed explicitly (numpyro 0.9.2 imports fine without it for our use).
#  - gcastle is installed from the repo root at rev a768c0a (the repo has no 'gcastle' subdirectory).
#  - torch is the CPU build. The lab GPU is an RTX PRO 4500 Blackwell; torch 1.12 has no kernels for it.

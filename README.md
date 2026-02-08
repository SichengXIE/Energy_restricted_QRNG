# Energy restricted prepare-and-measure scenarios

This code is applicable in semi-device independent frameworks with energy restriction in the state preparations. Use this code to compute:

  1. Success probability in state discrimination games (we call this Witness).
  2. Min-entropy for fixed observed probabilities or bounded state discrimination witness.
  3. Shannon entropy for fixed observed probabilities or bounded state discrimination withess.

This code uses a package to generate moment matrix semidefinite programming (SDP) relaxations. 
The package is called "MoMPy" and can be freely downloaded using pip.

## Suggested environment (circa 2022)

The repository does not pin exact dependency versions. Based on the libraries used and the
approximate upload timeframe, the following environment targets are a reasonable baseline
for reproducibility:

- Python 3.9 (recommended)
- numpy ~= 1.22
- scipy ~= 1.8
- cvxpy ~= 1.3
- chaospy ~= 4.3
- MoMPy (install via pip)

### Option A: pip + venv (Windows / macOS / Linux)

```bash
# Windows (PowerShell)
py -3.9 -m venv .venv
.\.venv\Scripts\activate
py -3.9 -m pip install --upgrade pip
py -3.9 -m pip install -r requirements.txt

# macOS / Linux
python3.9 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Option B: conda

```bash
conda create -n energy-qrng python=3.9
conda activate energy-qrng
pip install -r requirements.txt
```

### Common pitfalls

- Ensure you are using **Python 3.9** when installing dependencies. Newer Python versions (e.g., 3.13)
  may fail to build older numerical packages. If you have multiple Pythons installed, prefer
  `py -3.9 -m pip ...` on Windows to avoid accidentally using Python 3.13's pip.
- The requirements file is named **`requirements.txt`** (plural). If you see `No such file or directory`
  errors, double-check the filename and current directory.
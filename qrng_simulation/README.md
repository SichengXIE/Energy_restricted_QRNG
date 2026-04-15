# QRNG Design Simulations

This folder contains the engineering simulations and local output checks used during the QRNG design work. It is organized as a self-contained package inside the main repository so that the original theoretical code and the newer design-stage simulations remain clearly separated.

The package covers:

- physical-source modeling;
- digital extraction and basic statistical checks;
- driver-stack and mode-switch behavior;
- NAS-side workload modeling;
- local random-output generation and sanity checks.

## Directory Layout

```text
qrng_simulation/
├── README.md
├── requirements.txt
├── .gitignore
├── figures/
└── scripts/
    ├── chapter2_physical_source_simulation.py
    ├── chapter3_digital_logic_simulation.py
    ├── chapter4_driver_stack_simulation.py
    ├── chapter5_nas_workload_simulation.py
    ├── qrng_sim_core.py
    ├── qrng_local_test.py
    └── run_all_simulations.py
```

## Environment

- Python 3.10+
- `numpy`
- `Pillow`
- `scipy`

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

## Run All Simulations

Generate all figures and summary JSON files:

```bash
python3 scripts/run_all_simulations.py
```

## Local QRNG Output Test

Run a local A-path output test:

```bash
python3 scripts/qrng_local_test.py --track a --stage conditioned --bits 4096 --format hex
```

Run a local B-path output test:

```bash
python3 scripts/qrng_local_test.py --track b --stage conditioned --bits 4096 --format u32
```

Run both paths and save binary outputs:

```bash
python3 scripts/qrng_local_test.py --track both --bits 8192 --output-dir ./local_test_output
```

The local test runner prints a JSON report with:

- output preview values
- bit count and byte count
- ones ratio and bit bias
- runs and expected runs
- lag-1 correlation
- byte-level entropy and min-entropy estimates

## Scripts

### `chapter2_physical_source_simulation.py`

Physical-layer simulations:

- A-path minimum entropy versus CMRR
- B-path cross-channel correlation heatmap
- A-path PDF and B-path autocorrelation reference curves
- optional topology SVG figures

### `chapter3_digital_logic_simulation.py`

Digital-path simulations:

- A-path compression ratio versus entropy slack and bias
- B-path p-value heatmap
- entropy deficit counter timing waveform
- optional FPGA architecture SVG figure

### `chapter4_driver_stack_simulation.py`

Driver and switching simulations:

- blackout jitter figures
- queue occupancy timeline
- driver-stack and mode-switch diagrams

### `chapter5_nas_workload_simulation.py`

Workload-side simulations:

- NAS I/O versus random-service demand
- throughput deficit accumulation
- NAS-side call-flow diagram

### `qrng_sim_core.py`

Reusable simulation core:

- A-path raw and conditioned output generation
- B-path raw and conditioned output generation
- dense linear extraction and SHAKE-256 expansion
- quick self-check metrics

### `qrng_local_test.py`

Local CLI for:

- printing random output previews
- saving binary output files
- checking basic output statistics on A-path and B-path output

## Output

By default, generated figures and summary files are written to:

```text
figures/
```

The committed files in `figures/` are reference outputs generated from the current scripts. They can be regenerated locally with `scripts/run_all_simulations.py`.

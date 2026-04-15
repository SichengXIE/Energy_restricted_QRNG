# Energy-Restricted QRNG and Engineering Simulations

This repository now contains two related but distinct lines of work:

1. the original energy-restricted semi-device-independent analysis code for prepare-and-measure scenarios;
2. a newer `qrng_simulation/` package for engineering-side QRNG design simulations and local output checks.

The original codebase remains focused on witness bounds, min-entropy, and Shannon entropy under energy constraints. The new package extends the repository toward product-oriented validation for an FPGA-based SDI QRNG module.

## Repository Structure

- `Energy_restriced_QRNG_main.py`
  Original SDP-based analysis script for energy-restricted prepare-and-measure scenarios.
- `manuscript_data/`
  Data files used for the manuscript figures and analysis runs.
- `qrng_simulation/`
  Engineering simulations covering source behavior, digital extraction, driver behavior, workload-side modeling, and local output sanity checks.

## Original Research Scope

The original research code is applicable to semi-device-independent settings with energy restrictions on state preparation. It is used to compute:

1. success probabilities in state discrimination games;
2. min-entropy for fixed observed probabilities or bounded witness values;
3. Shannon entropy for fixed observed probabilities or bounded witness values.

This part of the repository depends on SDP relaxations generated through `MoMPy`.

## New QRNG Simulation Package

The `qrng_simulation/` folder adds an engineering validation layer that was not present in the original repository. It is intended for early-stage module design work, reproducible figure generation, and local output sanity checks.

The simulation package covers:

- physical-source behavior for two QRNG paths;
- digital extraction and conditioning behavior;
- driver-stack and mode-switch timing behavior;
- NAS-side workload and random-service demand;
- local output generation with basic statistical checks.

## Difference and Progress

The key difference is scope. The original repository studies security-relevant bounds in an energy-restricted SDI model. The new package studies whether a concrete QRNG design can be organized, simulated, and evaluated as an engineering system.

The main progress introduced by this update is:

- moving from certification-oriented witness calculations toward end-to-end module validation;
- adding simulation coverage from the physical source to software-facing interfaces;
- adding a reproducible local output test path for design-stage sanity checking;
- separating theoretical research code from product-facing simulation code without disturbing the original workflow.

## Quick Start

For the original theory code:

```bash
python3 -m pip install -r requirements.txt
```

For the QRNG simulation package:

```bash
cd qrng_simulation
python3 -m pip install -r requirements.txt
python3 scripts/run_all_simulations.py
python3 scripts/qrng_local_test.py --track both --bits 8192 --output-dir ./local_test_output
```

## Notes

The engineering simulation package is an extension, not a replacement, of the original energy-restricted SDI work. The two parts of the repository address different stages of the same broader QRNG development path: theoretical security analysis on one side and implementation-oriented design validation on the other.

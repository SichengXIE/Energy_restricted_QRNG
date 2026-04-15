from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    ("chapter2_physical_source_simulation.py", ["--locale", "en", "--with-svg"]),
    ("chapter3_digital_logic_simulation.py", ["--locale", "en", "--with-svg"]),
    ("chapter4_driver_stack_simulation.py", ["--locale", "en"]),
    ("chapter5_nas_workload_simulation.py", ["--locale", "en"]),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full QRNG simulation set.")
    parser.add_argument("--locale", choices=("en", "zh"), default="en")
    parser.add_argument("--output-dir", default=str(ROOT / "figures"))
    parser.add_argument("--skip-svg", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for script_name, script_args in SCRIPTS:
        script_path = ROOT / "scripts" / script_name
        cmd = [sys.executable, str(script_path), "--locale", args.locale, "--output-dir", args.output_dir]
        if not args.skip_svg and "--with-svg" in script_args:
            cmd.append("--with-svg")
        print(" ".join(cmd))
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()

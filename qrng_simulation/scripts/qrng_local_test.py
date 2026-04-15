from __future__ import annotations

import argparse
import json
from pathlib import Path

from qrng_sim_core import (
    bits_to_bytes,
    generate_track_bits,
    preview_values,
    quick_self_check,
    save_binary_output,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run local QRNG output checks."
    )
    parser.add_argument("--track", choices=("a", "b", "both"), default="both")
    parser.add_argument("--stage", choices=("conditioned", "raw"), default="conditioned")
    parser.add_argument("--bits", type=int, default=4096, help="Output bits per selected track.")
    parser.add_argument("--seed", type=int, default=20260414)
    parser.add_argument("--cmrr-db", type=float, default=40.0, help="A-path only.")
    parser.add_argument(
        "--format",
        choices=("hex", "u32", "bits"),
        default="hex",
        help="Preview format for the first few output groups.",
    )
    parser.add_argument("--show", type=int, default=6, help="How many preview groups to print.")
    parser.add_argument("--output-dir", default=None, help="Optional directory for binary output and report.")
    return parser.parse_args()


def run_one_track(track: str, args: argparse.Namespace) -> dict[str, object]:
    conditioned = args.stage == "conditioned"
    bits = generate_track_bits(
        track=track,
        out_bits=args.bits,
        seed=args.seed if track == "a" else args.seed + 1000,
        conditioned=conditioned,
        cmrr_db=args.cmrr_db,
    )
    data = bits_to_bytes(bits)
    summary = quick_self_check(bits)
    summary.update(
        {
            "track": track,
            "stage": args.stage,
            "seed": args.seed if track == "a" else args.seed + 1000,
            "cmrr_db": args.cmrr_db if track == "a" else None,
            "preview_format": args.format,
            "preview": preview_values(data, args.format, args.show),
        }
    )
    if args.output_dir:
        path = save_binary_output(Path(args.output_dir), track, data)
        summary["output_file"] = str(path)
        summary["output_file_exists"] = path.exists()
    return summary


def main() -> None:
    args = parse_args()
    tracks = ["a", "b"] if args.track == "both" else [args.track]
    report = {
        "bits_per_track": args.bits,
        "stage": args.stage,
        "tracks": [run_one_track(track, args) for track in tracks],
    }

    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "summary.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["summary_file"] = str(report_path)
        report["summary_file_exists"] = report_path.exists()

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

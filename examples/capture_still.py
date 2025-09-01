#!/usr/bin/env python3
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

def require(cmd: str):
    if shutil.which(cmd) is None:
        print(f"Error: '{cmd}' not found in PATH. Did you install rpicam-apps?", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Capture a still image using rpicam-still.")
    parser.add_argument("--output", "-o", type=Path, default=Path("capture.jpg"), help="Output image path")
    parser.add_argument("--width", type=int, default=2028, help="Capture width")
    parser.add_argument("--height", type=int, default=1520, help="Capture height")
    parser.add_argument("--quality", type=int, default=90, help="JPEG quality (1-100)")
    parser.add_argument("--timeout", type=int, default=1000, help="Preview time before capture (ms)")
    args = parser.parse_args()

    require("rpicam-still")

    cmd = [
        "rpicam-still",
        "-o", str(args.output),
        "--width", str(args.width),
        "--height", str(args.height),
        "--quality", str(args.quality),
        "-t", str(args.timeout),
    ]

    print("Capturing:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("Stopped by user.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import shutil
import subprocess
import sys

def require(cmd: str):
    if shutil.which(cmd) is None:
        print(f"Error: '{cmd}' not found in PATH. Did you install rpicam-apps?", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Open a live preview using rpicam-vid.")
    parser.add_argument("--width", type=int, default=1280, help="Preview width")
    parser.add_argument("--height", type=int, default=720, help="Preview height")
    parser.add_argument("--fps", type=int, default=30, help="Framerate")
    parser.add_argument("--timeout", type=int, default=0, help="Duration in ms (0 = infinite)")
    args = parser.parse_args()

    require("rpicam-vid")

    cmd = [
        "rpicam-vid",
        "-t", str(args.timeout),
        "--width", str(args.width),
        "--height", str(args.height),
        "--framerate", str(args.fps),
    ]

    print("Launching:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("Stopped by user.")

if __name__ == "__main__":
    main()

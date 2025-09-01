#!/usr/bin/env python3
import subprocess

def main():
    cmd = [
        "rpicam-vid",
        "--codec", "mjpeg",
        "-t", "0",
        "--nopreview",
        "-o", "-"
    ]

    player = [
        "mpv",
        "--demuxer=lavf",
        "--demuxer-lavf-format=mjpeg",
        "--profile=low-latency",
        "--no-cache",
        "--untimed",
        "-"
    ]

    # Starte rpicam-vid und leite direkt an mpv weiter
    proc1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    subprocess.run(player, stdin=proc1.stdout)

if __name__ == "__main__":
    main()

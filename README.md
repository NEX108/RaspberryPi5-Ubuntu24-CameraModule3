# Raspberry Pi 5 + Ubuntu 24.04 + Camera Module 3

This repository documents how to get the **Raspberry Pi Camera Module 3
(IMX708)** working on a **Raspberry Pi 5** running **Ubuntu 24.04**.\
Ubuntu's default `libcamera` (from `apt`) is the *upstream* version and
typically does **not** recognize Pi cameras on Ubuntu.\
**Solution:** build the **Raspberry Pi fork of `libcamera`** and the
**`rpicam-apps`** from source, then use the provided Python scripts
(inside a venv).

> References: Raspberry Pi libcamera fork & rpicam-apps docs; community
> notes confirming the fork requirement on Ubuntu.

------------------------------------------------------------------------

## TL;DR

1.  Edit `/boot/firmware/config.txt` and add:

        camera_auto_detect=0
        dtoverlay=imx708

    Reboot.

2.  Build and install **RPi `libcamera`** (Meson/Ninja) with Raspberry
    Pi pipelines enabled.

3.  Build and install **`rpicam-apps`** (CMake).

4.  Create a Python **venv** and run the example scripts:

    -   `examples/live_feed.py` --- live preview
    -   `examples/capture_still.py` --- capture a JPEG

------------------------------------------------------------------------

(Full installation guide and examples will follow in detail.)

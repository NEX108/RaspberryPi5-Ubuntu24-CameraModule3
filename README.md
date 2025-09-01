# Raspberry Pi 5 + Ubuntu 24.04 + Camera Module 3

This repository documents how to get the **Raspberry Pi Camera Module 3 (IMX708)** working on a **Raspberry Pi 5** running **Ubuntu 24.04**.  
Ubuntu’s default `libcamera` (from `apt`) is the *upstream* version and often does **not** recognize Pi cameras on Ubuntu.  
**Solution:** build the **Raspberry Pi fork of `libcamera`** and the **`rpicam-apps`** from source, then use the provided Python scripts (inside a venv).

> This README is written to be copy-paste friendly for a fresh Ubuntu 24.04 image on a Pi 5.

---

## TL;DR
1. Edit `/boot/firmware/config.txt` and add (depending on which CSI port you use):
   ```
   camera_auto_detect=0
   dtoverlay=imx708,cam0   # front connector (bus 10)
   # or: dtoverlay=imx708,cam1   # rear connector (bus 11)
   ```
   Reboot.
2. Build and install **RPi `libcamera`** (Meson/Ninja) with Raspberry Pi pipelines enabled.
3. Build and install **`rpicam-apps`** (Meson).
4. Create a Python **venv** and run the example scripts:
   - `examples/live_feed.py` — live preview
   - `examples/capture_still.py` — capture a JPEG

---

## 1) System preparation (fresh Ubuntu 24.04 on Pi 5)

Update and install build dependencies:

```bash
sudo apt update && sudo apt upgrade -y

# Core build tools & helpers
sudo apt install -y git build-essential pkg-config meson ninja-build cmake     python3-venv python3-dev python3-pip pybind11-dev

# libcamera dependencies
sudo apt install -y libboost-dev libgnutls28-dev libssl-dev openssl libtiff-dev     libglib2.0-dev libgstreamer-plugins-base1.0-dev

# Python modules needed for the libcamera build system
sudo apt install -y python3-ply python3-yaml

# rpicam-apps dependencies
sudo apt install -y libboost-program-options-dev libexif-dev libavcodec-dev

# Player for live preview (used in examples/live_feed.py)
sudo apt install -y mpv

# optinal: Tools for I²C / V4L2 debugging
sudo apt install -y i2c-tools v4l-utils

# Useful/optional for previews, codecs, KMS etc.
sudo apt install -y libdrm-dev libjpeg-dev libpng-dev
```

> If you don’t need GStreamer, you may disable it during Meson configure and omit the `libglib2.0-dev` / `libgstreamer-plugins-base1.0-dev` packages.

---

## 2) Enable the Camera Module 3 (IMX708) on Ubuntu

Edit the firmware config:

```bash
sudo nano /boot/firmware/config.txt
```

Append **exactly** these lines (keep existing content as is).  
Use `cam0` for the front connector (I²C bus 10), or `cam1` for the rear connector (I²C bus 11):

```ini
camera_auto_detect=0
dtoverlay=imx708,cam0
```

---

### Example config.txt change

In `/boot/firmware/config.txt` you may already see:  

```ini
# Autoload overlays for any recognized cameras or displays that are attached
# to the CSI/DSI ports. Please note this is for libcamera support, *not* for
# the legacy camera stack
camera_auto_detect=1
display_auto_detect=1
```

Change it to:  

```ini
camera_auto_detect=0
dtoverlay=imx708,cam0
display_auto_detect=1
```

**Diff-style view:**  

```diff
- camera_auto_detect=1
+ camera_auto_detect=0
+ dtoverlay=imx708,cam0
  display_auto_detect=1
```

Save, then reboot:

```bash
sudo reboot
```

---

### Video group permissions

Make sure your user can access the video devices:

```bash
sudo usermod -aG video $USER
# Log out/in again or reboot
```

No output is shown if this succeeds (that’s normal).

### Verification

After reboot, check:

```bash
groups
```

Example output:

```
username adm cdrom sudo dip plugdev lxd video
```

Here, `video` confirms that the user is in the correct group.

---

## 3) Build Raspberry Pi’s `libcamera` fork

```bash
# Get the RPi libcamera fork
git clone https://github.com/raspberrypi/libcamera.git
cd libcamera

# Configure the build (enable Raspberry Pi pipelines & Python bindings)
meson setup build --buildtype=release \
  -Dpipelines=rpi/vc4,rpi/pisp \
  -Dipas=rpi/vc4,rpi/pisp \
  -Dv4l2=enabled -Dgstreamer=enabled \
  -Dtest=false -Dlc-compliance=disabled -Dcam=disabled -Dqcam=disabled \
  -Ddocumentation=disabled -Dpycamera=enabled

# Compile & install
ninja -C build
sudo ninja -C build install
sudo ldconfig

cd ..
```

**Notes**  
- Always build `rpicam-apps` **after** (re)building this libcamera fork to keep ABI compatibility.  
- If Meson complains about missing dependencies, install the suggested `-dev` packages and re-run `meson setup` (or `meson setup --reconfigure build`).

---

## 4) Build `rpicam-apps`

```bash
git clone https://github.com/raspberrypi/rpicam-apps.git
cd rpicam-apps
meson setup build --buildtype=release
ninja -C build
sudo ninja -C build install
sudo ldconfig

# Quick smoke tests (optional; may fail if camera not connected/configured yet)
rpicam-hello --list-cameras || true
rpicam-still -o test.jpg || true
rpicam-vid -t 2000 || true
cd ..
```

---

## 5) Python virtual environment & examples

Create and activate a local venv in the repository root (clone of  GitHub repo):

```bash
# clone Repo
cd ~
git clone https://github.com/NEX108/RaspberryPi5-Ubuntu24-CameraModule3.git
cd RaspberryPi5-Ubuntu24-CameraModule3
# create venv
python3 -m venv .venv
source .venv/bin/activate
python --version
pip install --upgrade pip
```

Run the examples shipped in `examples/`:

```bash
# Live preview (window opens; Ctrl+C to stop)
python examples/live_feed.py

# Capture a still image
python examples/capture_still.py
```

> These Python scripts call `rpicam-vid` / `rpicam-still` via `subprocess` to keep things simple and robust.  
> You can adjust resolution/FPS using the CLI arguments shown above.

---

## 6) Verifying the installation

```bash
# See detected cameras
rpicam-hello --list-cameras

# Basic still capture
rpicam-still -o test.jpg
```

If you see `no cameras available`, check the **Troubleshooting** section below.

---

## 7) Headless / Wayland tips (optional)

If you don’t have a desktop session or preview windows cause issues, stream to stdout and pipe into a player:

```bash
# Example: stream H.264 to stdout and play with mpv
rpicam-vid --codec h264 --profile high --inline -t 0 -o - | mpv -
```

---

## 8) Troubleshooting

- **“no cameras available”**  
  • Re-check `/boot/firmware/config.txt` (`camera_auto_detect=0`, `dtoverlay=imx708,cam0` or `cam1`), cabling, and reboot.  
  • Ensure you built and installed the **RPi libcamera fork** (not upstream).  
  • Verify permissions: your user is in the `video` group.  
  • Kernel messages:  
    ```bash
    sudo dmesg | grep -i imx708
    ```  
  • If still failing, try the *other CSI connector*:  
    ```ini
    dtoverlay=imx708,cam1
    ```  
    Then power-cycle and check again:
    ```bash
    sudo i2cdetect -y 10   # cam0 → expect 0x1a
    sudo i2cdetect -y 11   # cam1 → expect 0x1a
    ```

- **ABI mismatch / apps crash or cannot start**  
  • If you update/rebuild `libcamera`, **rebuild `rpicam-apps` right after**.  
  • Run `sudo ldconfig` after installs.

- **Missing dependencies during Meson**  
  • Carefully read the error; install the suggested `-dev` packages and retry.  
  • You can clean the build directories:  
    ```bash
    rm -rf libcamera/build rpicam-apps/build
    ```

- **Preview window issues (Wayland/KMS)**  
  • Try headless pipeline (`--nopreview` or `-o -`) and watch via `mpv`.  
  • Ensure you are on the Pi 5 HDMI output; avoid remote X forwarding.
  
- **Preview works with MJPEG but not H.264**
  • Install FFmpeg: `sudo apt install -y ffmpeg`
  • Or explicitly use MJPEG codec (`--codec mjpeg`), which works out-of-the-box.


---

## 9) Repository layout

```
RaspberryPi5-Ubuntu24-CameraModule3/
├─ README.md
├─ .gitignore
└─ examples/
   ├─ live_feed.py
   └─ capture_still.py
```

---

## 10) Updating / Rebuilding

When you `git pull` new changes for the forks, rebuild in this order:

```bash
# Rebuild libcamera
cd libcamera
meson setup --reconfigure build --buildtype=release \
  -Dpipelines=rpi/vc4,rpi/pisp \
  -Dipas=rpi/vc4,rpi/pisp \
  -Dv4l2=enabled -Dgstreamer=enabled \
  -Dtest=false -Dlc-compliance=disabled -Dcam=disabled -Dqcam=disabled \
  -Ddocumentation=disabled -Dpycamera=enabled
ninja -C build
sudo ninja -C build install
sudo ldconfig
cd ..

# Rebuild rpicam-apps
cd rpicam-apps/build
ninja clean
meson setup --reconfigure build --buildtype=release
ninja -C build
sudo ninja -C build install
sudo ldconfig
cd ../..
```

---

## References & Acknowledgements

- Raspberry Pi `libcamera` fork and `rpicam-apps`  
- Community notes confirming the need for the RPi fork on Ubuntu (e.g. Reddit thread: Raspberry Pi 5 + Ubuntu 24.04 + Pi Camera 3)

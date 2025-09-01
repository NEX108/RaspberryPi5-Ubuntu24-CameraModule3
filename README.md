# Raspberry Pi 5 + Ubuntu 24.04 + Camera Module 3

This repository documents how to get the **Raspberry Pi Camera Module 3 (IMX708)** working on a **Raspberry Pi 5** running **Ubuntu 24.04**.  
Ubuntu’s default `libcamera` (from `apt`) is the *upstream* version and often does **not** recognize Pi cameras on Ubuntu.  
**Solution:** build the **Raspberry Pi fork of `libcamera`** and the **`rpicam-apps`** from source, then use the provided Python scripts (inside a venv).

> This README is written to be copy‑paste friendly for a fresh Ubuntu 24.04 image on a Pi 5.

---

## TL;DR
1. Edit `/boot/firmware/config.txt` and add:
   ```
   camera_auto_detect=0
   dtoverlay=imx708
   ```
   Reboot.
2. Build and install **RPi `libcamera`** (Meson/Ninja) with Raspberry Pi pipelines enabled.
3. Build and install **`rpicam-apps`** (CMake).
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

# libcamera dependencies (common on Ubuntu 24.04)
sudo apt install -y libboost-dev libgnutls28-dev libssl-dev openssl libtiff-dev     libglib2.0-dev libgstreamer-plugins-base1.0-dev

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
Append **exactly** these lines (keep existing content as is):
```
camera_auto_detect=0
dtoverlay=imx708
```
Save, then:

```bash
sudo reboot
```

Make sure your user can access the video devices:

```bash
sudo usermod -aG video $USER
# Log out/in again or reboot
```

---

## 3) Build Raspberry Pi’s `libcamera` fork

```bash
# Get the RPi libcamera fork
git clone https://github.com/raspberrypi/libcamera.git
cd libcamera

# Configure the build (enable Raspberry Pi pipelines & Python bindings)
meson setup build --buildtype=release   -Dpipelines=rpi/vc4,rpi/pisp   -Dipas=rpi/vc4,rpi/pisp   -Dv4l2=true -Dgstreamer=enabled   -Dtest=false -Dlc-compliance=disabled -Dcam=disabled -Dqcam=disabled   -Ddocumentation=disabled -Dpycamera=enabled

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
mkdir -p build && cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
make -j$(nproc)
sudo make install
sudo ldconfig

# Quick smoke tests (optional; may fail if camera not connected/configured yet)
rpicam-hello --list-cameras || true
rpicam-still -o test.jpg || true
rpicam-vid -t 2000 || true
cd ../..
```

---

## 5) Python virtual environment & examples

Create and activate a local venv in the repository root (clone of your GitHub repo):

```bash
python3 -m venv .venv
source .venv/bin/activate
python --version
pip install --upgrade pip
```

Run the examples shipped in `examples/`:

```bash
# Live preview (window opens; Ctrl+C to stop)
python examples/live_feed.py --width 1280 --height 720 --fps 30

# Capture a still image
python examples/capture_still.py --output capture.jpg --width 2028 --height 1520
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

# Basic video preview (0 = infinite; press Ctrl+C)
rpicam-vid -t 0
```

If you see `no cameras available`, check the **Troubleshooting** section below.

---

## 7) Headless / Wayland tips (optional)

If you don’t have a desktop session or preview windows cause issues, stream to stdout and pipe into a player:

```bash
# Example: stream H.264 to stdout and play with mpv
rpicam-vid --codec h264 --profile high --inline -t 0 -o - | mpv -
```

For pure capture without preview, use `rpicam-still` with a short timeout (e.g. `-t 1000`).

---

## 8) Troubleshooting

- **“no cameras available”**  
  • Re-check `/boot/firmware/config.txt` (`camera_auto_detect=0`, `dtoverlay=imx708`), cabling, and reboot.  
  • Ensure you built and installed the **RPi libcamera fork** (not upstream).  
  • Verify permissions: your user is in the `video` group.  
  • Kernel messages: `dmesg | grep -i imx708`.

- **ABI mismatch / apps crash or cannot start**  
  • If you update/rebuild `libcamera`, **rebuild `rpicam-apps` right after**.  
  • Run `sudo ldconfig` after installs.

- **Missing dependencies during Meson/CMake**  
  • Carefully read the error; install the suggested `-dev` packages and retry.  
  • You can clean the build directories: `rm -rf libcamera/build rpicam-apps/build`.

- **Preview window issues (Wayland/KMS)**  
  • Try headless pipeline (`--stdout`) and watch via `mpv` or save a still first.  
  • Make sure you’re on the Pi 5 HDMI output; avoid remote X forwarding for previews.

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
meson setup --reconfigure build --buildtype=release   -Dpipelines=rpi/vc4,rpi/pisp -Dipas=rpi/vc4,rpi/pisp   -Dv4l2=true -Dgstreamer=enabled   -Dtest=false -Dlc-compliance=disabled -Dcam=disabled -Dqcam=disabled   -Ddocumentation=disabled -Dpycamera=enabled
ninja -C build
sudo ninja -C build install
sudo ldconfig
cd ..

# Rebuild rpicam-apps
cd rpicam-apps/build
make clean
cmake -DCMAKE_BUILD_TYPE=Release ..
make -j$(nproc)
sudo make install
sudo ldconfig
cd ../..
```

---

## References & Acknowledgements

- Raspberry Pi `libcamera` fork and `rpicam-apps`  
- Community notes confirming the need for the RPi fork on Ubuntu (e.g. Reddit thread: Raspberry Pi 5 + Ubuntu 24.04 + Pi Camera 3)

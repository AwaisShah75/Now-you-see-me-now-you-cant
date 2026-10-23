# Now You See Me, Now You Can't

A CPU-powered webcam illusion: close your fist and disappear from the live video. Open your hand to reset, then close it again to return.

Built with **Python, OpenCV, MediaPipe, and Tkinter**. Includes an unobstructed, resizable preview and automatic MP4 recording.

## Features

- Closed-fist gesture with a brief 0.35-second hold and open-hand reset.
- Background capture and smooth vanish/reappear transitions.
- Large video preview with controls outside the image.
- CPU hand tracking; no dedicated GPU required.
- Automatic timestamped **1280 × 720 MP4** recordings on every launcher run.
- Separate camera, hand-detection, and recording threads to keep the interface responsive.
- Keyboard and button controls if hand tracking is unavailable.

## Quick start — Windows

1. Install **64-bit Python 3.11 or 3.12** from [python.org](https://www.python.org/downloads/windows/), including the Python launcher.
2. Clone this repository onto your preferred drive, for example D:, or download and extract the ZIP there.
3. Double-click **start.bat**.

The first run creates `.venv`, installs dependencies, and downloads the official hand model. Internet is needed for that setup. Later launches use the local model.

```powershell
git clone https://github.com/AwaisShah75/Now-you-see-me-now-you-cant.git
cd Now-you-see-me-now-you-cant
.\start.bat
```

The launcher keeps the environment, model, recordings, installation temporary files, Python bytecode, and Matplotlib cache inside the project folder. Put the project on D: to keep those files there. No `.env` file or global PATH modification is needed; an installed Python interpreter is still required.

## Make yourself disappear

1. Keep the laptop/camera still and use steady lighting.
2. Click **Capture background** or press **B**. Leave the frame during the five-second countdown and remain out until capture completes.
3. Step into view. Close your hand into a **fist** for about **0.35 seconds**.
4. Open your hand to reset the gesture, then close it again to reappear.

Keep your fingers visible. The thumb position is flexible. Estimated 3D landmark distances tolerate hand rotation, but extreme angles, occlusion, and poor lighting can still prevent detection.

| Control | Action |
| --- | --- |
| Capture background / B | Capture the empty scene after a countdown |
| Vanish or Reappear / Space | Toggle the effect |
| Closed fist | Toggle after a brief hold |
| Open hand | Reset gesture detection for the next fist |
| Escape / Q / window close | Exit and finalize the recording |

## Automatic recording

Each `start.bat` launch creates a new file:

```text
recordings/session_YYYY-MM-DD_HH-MM-SS_microseconds.mp4
```

Recordings contain the mirrored camera image and vanish effect, **without interface text or buttons**. They are silent; the microphone is not used. Close the app normally so the MP4 is finalized. The window title indicates when recording is enabled.

- Output: **1280 × 720**, **30 FPS**, MPEG-4 video in an MP4 container.
- Default capture: **640 × 480**, scaled to the recording size with aspect ratio preserved. This is a 720p file, not extra native camera detail; black bars may appear.
- Native HD capture is optional and can lower camera/preview FPS.
- The recorder repeats the latest frame when capture is slower than the output rate. Encoding hardware and disk speed can affect timing.

```powershell
# Disable recording for this launch
.\start.bat --no-record

# Request native HD from the webcam
.\start.bat --width 1280 --height 720

# Select another webcam
.\start.bat --camera 1

# Reduce capture and inference size on slower laptops
.\start.bat --width 480 --height 360 --gesture-width 256

# Use buttons and keyboard without hand tracking
.\start.bat --no-gestures
```

## Performance and verification

Short local webcam checks measured **26.8 FPS** with the large preview and **26.9 FPS** with 720p MP4 recording enabled at default capture resolution. Native 1280 × 720 camera capture measured about **20 FPS** on the same laptop. These are development measurements, not a guarantee across hardware or lighting conditions. The interface displays the actual main-loop FPS; hand inference is capped at **10 Hz**.

Verified: Python compilation, dependency consistency, CPU model initialization, five gesture-state tests, and decoding a generated MP4 at 1280 × 720 / 30 FPS. Real fist recognition still depends on your hand position and camera conditions.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m pip check
```

## How it works

The app saves a clean background image from twelve empty-scene samples. On a fist trigger, it blends the live feed into that saved image over about 0.65 seconds. The camera continues feeding hand detection while the background is displayed, so a second gesture can restore the live image.

This is a **clean-background illusion**: it replaces the entire visible scene, including other people or moving objects. It does not segment only one person, invent the background behind you, or provide a virtual camera for meeting apps. Moving the camera or changing lighting requires another background capture. Video processing runs locally; MP4s are saved locally and are not uploaded by the app.

See [architecture and implementation notes](docs/ARCHITECTURE.md).

## Troubleshooting

| Problem | Try this |
| --- | --- |
| Camera will not open | Close other camera apps, check Windows camera permissions, or use `--camera 1` |
| Gesture does not trigger | Show the fingers clearly, hold a fist briefly, then fully open your hand before trying again; use Space as a fallback |
| Background looks wrong | Hold the camera still, capture again, and stay out until capture completes |
| Low FPS | Improve lighting, use default capture rather than native HD, or lower capture dimensions |
| Model download fails | Check internet access and rerun; Space/buttons remain available without the model |
| Recording will not play | Exit normally and wait for the app to close; forced termination can leave an unfinished MP4 |

## Project files

```text
app.py                  Camera, gesture worker, effect, and application lifecycle
snap.py                 Closed-fist detection and gesture state machine
studio_ui.py            Native Tkinter preview and controls
recording.py            Background MP4 writer
start.bat               Windows setup and automatic-recording launcher
requirements.txt        Python dependencies
tests/test_snap.py      Gesture timing, reset, tracking loss, and rotation tests
docs/ARCHITECTURE.md    Pipeline and implementation details
```

`.venv/`, `.runtime/`, `models/`, and `recordings/` are generated locally and excluded from Git.

## Built with

[OpenCV](https://opencv.org/) · [MediaPipe Hand Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/python) · [NumPy](https://numpy.org/) · [Pillow](https://python-pillow.org/) · Tkinter

The Google hand model is downloaded from its official MediaPipe model distribution. Third-party libraries and models retain their respective licenses.

# Architecture

## Video pipeline

```text
Webcam -> CameraReader (latest frame only) -> main loop -> mirrored frame
                                                     -> small hand inference frame
                                                     -> background blend
                                                     -> Recorder (latest output only)
                                                     -> Studio preview
```

`CameraReader` captures independently of UI rendering and uses a one-frame queue. This bounds memory and avoids a growing delay when rendering slows down.

`Hands` uses MediaPipe Hand Landmarker in VIDEO mode with an explicit CPU delegate and one tracked hand. Its input is reduced to 320 pixels wide by default. Calls are limited to approximately 10 Hz. Capture timestamps become monotonically increasing inference timestamps.

`snap.py` retains its original module/class names for compatibility, but detects a **closed fist**, not a pinch or acoustic snap. For the four fingers it compares fingertip-to-wrist distance with middle-joint-to-wrist distance in landmark 3D coordinates. At least three fingers must be curled and none may be strongly extended. A 0.35-second hold triggers once. Three extended fingers rearm the detector, with a 1.2-second cooldown. Losing tracking cancels a partial hold but does not rearm a triggered fist.

## Background effect

The main loop mirrors and resizes camera frames. Capture starts after a five-second delay, then uses a median of twelve frames to construct the background. A transition moves between live output and the captured background over about 0.65 seconds. Backgrounds are kept in memory, not saved to disk.

## Interface

Tkinter runs on the main thread. The video scales to the available area without changing its aspect ratio. Pillow updates the existing Tk image when dimensions stay the same. Controls and status are outside the image, so recordings contain no interface graphics.

## Recording

`Recorder` writes 1280x720, 30 FPS MP4 using OpenCV's `mp4v` codec. It keeps only the newest effect frame, resizes it with aspect ratio preserved, and adds black bars if needed. A monotonic clock schedules output frames; repeated source frames preserve playback timing when the camera is slower than the recording rate. Sustained encoding overload can still fall behind real time.

File names include the launch date/time and microseconds to avoid collisions. The worker releases the writer on shutdown; zero-frame files are removed. Recording errors are surfaced to the main loop. Close the app normally to finalize the MP4 container.

## Storage and setup

The Windows launcher sets TEMP, TMP, PIP_CACHE_DIR, PYTHONPYCACHEPREFIX, and MPLCONFIGDIR to locations under the project folder before creating/installing the environment or launching Python. Pip download caching is disabled during installation. The launcher enables recording; direct `python app.py` requires `--record` to enable it.

The hand model is downloaded on first use to a temporary `.download` file and renamed after completion. Camera input and inference use no cloud video processing. MediaPipe may produce its own diagnostic/telemetry messages; the app does not upload saved recordings.

## Verification scope

Gesture tests use synthetic landmarks to verify timing, latching, rearming, tracking loss, and rotation. They do not measure model accuracy on real hands. Webcam FPS and codec checks were short local manual benchmarks, not hardware-independent guarantees.

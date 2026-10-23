"""CPU webcam vanish effect. All camera processing stays on this computer."""
import argparse
import queue
import threading
import time
import urllib.request
from pathlib import Path

import cv2
import numpy as np

from snap import SnapDetector
from studio_ui import Studio
from recording import Recorder

MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'


class CameraReader(threading.Thread):
    """Capture while the UI paints; keep the most recent frame only."""
    def __init__(self, cap):
        super().__init__(daemon=True)
        self.cap = cap
        self.frames = queue.Queue(maxsize=1)
        self.stop = threading.Event()

    def run(self):
        while not self.stop.is_set():
            ok, frame = self.cap.read()
            if not ok:
                break
            try:
                self.frames.get_nowait()
            except queue.Empty:
                pass
            try:
                self.frames.put_nowait(frame)
            except queue.Full:
                pass

    def read(self):
        try:
            return True, self.frames.get(timeout=0.2)
        except queue.Empty:
            return False, None


class Hands(threading.Thread):
    def __init__(self, model):
        super().__init__(daemon=True)
        self.model = model
        self.frames = queue.Queue(maxsize=1)
        self.trigger = threading.Event()
        self.stop = threading.Event()
        self.status = 'Loading hand detector'
        self.error = None
        self.progress = 0.0

    def run(self):
        try:
            import mediapipe as mp
            from mediapipe.tasks.python import BaseOptions
            from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
            options = HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(self.model), delegate=BaseOptions.Delegate.CPU),
                running_mode=RunningMode.VIDEO, num_hands=1,
                min_hand_detection_confidence=0.5, min_tracking_confidence=0.5)
            detector = SnapDetector()
            last_stamp = 0
            with HandLandmarker.create_from_options(options) as hands:
                while not self.stop.is_set():
                    inference_started = time.perf_counter()
                    try:
                        frame, captured = self.frames.get(timeout=0.1)
                    except queue.Empty:
                        continue
                    stamp = max(last_stamp + 1, int(captured * 1000))
                    last_stamp = stamp
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    result = hands.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), stamp)
                    points = result.hand_landmarks[0] if result.hand_landmarks else None
                    fired = detector.update(points, captured)
                    self.progress = detector.progress
                    self.status = ('Open your hand to reset.' if detector.latched else 'Close your fist and hold briefly.') if points else 'Bring either hand into view'
                    if fired:
                        self.trigger.set()
                    self.stop.wait(max(0, 0.10 - (time.perf_counter() - inference_started)))
        except Exception as exc:
            self.error = str(exc)
            self.status = 'Hand detector unavailable; use SPACE'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--camera', type=int, default=0)
    parser.add_argument('--width', type=int, default=640)
    parser.add_argument('--height', type=int, default=480)
    parser.add_argument('--gesture-width', type=int, default=320)
    parser.add_argument('--no-gestures', action='store_true')
    parser.add_argument('--record', dest='record', action='store_true', help='Automatically save a 720p MP4')
    parser.add_argument('--no-record', dest='record', action='store_false')
    parser.set_defaults(record=False)
    args = parser.parse_args()
    if min(args.width, args.height, args.gesture_width) < 64:
        parser.error('Image dimensions must be at least 64')
    cv2.setNumThreads(2)
    worker = None
    recorder = None
    if not args.no_gestures:
        model = Path(__file__).parent / 'models' / 'hand_landmarker.task'
        if not model.exists():
            print('Downloading hand model (first run only)...')
            model.parent.mkdir(exist_ok=True)
            temporary = model.with_suffix('.download')
            try:
                with urllib.request.urlopen(MODEL_URL, timeout=60) as response:
                    temporary.write_bytes(response.read())
                temporary.replace(model)
            except Exception as exc:
                temporary.unlink(missing_ok=True)
                print(f'Model download failed: {exc}. SPACE still works.')
        if model.exists():
            worker = Hands(model)
            worker.start()
    cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW) if __import__('os').name == 'nt' else cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        cap.release()
        cap = cv2.VideoCapture(args.camera)
    try:
        if not cap.isOpened():
            raise RuntimeError('Cannot open webcam. Close other camera apps or try --camera 1.')
        if args.record:
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if args.record:
            recorder = Recorder(Path(__file__).parent / 'recordings')
            recorder.start()
            print(f'Recording HD MP4: {recorder.path}')
        reader = CameraReader(cap)
        reader.start()
        background = None
        capture_at = None
        samples = []
        hidden = False
        fade = 0.0
        previous = time.perf_counter()
        fps = 0.0
        failed = 0
        studio = Studio()
        if recorder:
            studio.root.title('Now You See Me | Recording HD MP4')
        while True:
            ok, frame = reader.read()
            now = time.perf_counter()
            if not ok:
                failed += 1
                if failed > 15:
                    raise RuntimeError('Webcam stopped delivering frames.')
                continue
            failed = 0
            frame = cv2.flip(cv2.resize(frame, (args.width, args.height)), 1)
            dt = max(now - previous, 0.001)
            previous = now
            fps = 1 / dt if not fps else fps * 0.92 + (1 / dt) * 0.08
            if worker and not worker.stop.is_set():
                small = cv2.resize(frame, (args.gesture_width, int(args.height * args.gesture_width / args.width)))
                try:
                    worker.frames.put_nowait((small, now))
                except queue.Full:
                    pass
            if capture_at is not None and now >= capture_at:
                samples.append(frame.copy())
                if len(samples) >= 12:
                    background = np.median(np.stack(samples), axis=0).astype(np.uint8)
                    capture_at = None
                    samples = []
                    hidden = False
                    fade = 0
            if worker and worker.trigger.is_set():
                worker.trigger.clear()
                if background is not None and capture_at is None:
                    hidden = not hidden
            fade = float(np.clip(fade + (dt / 0.65) * (1 if hidden else -1), 0, 1))
            output = cv2.addWeighted(frame, 1 - fade, background, fade, 0) if background is not None else frame.copy()
            if recorder:
                if recorder.error:
                    raise RuntimeError(f'Recording failed: {recorder.error}')
                recorder.submit(output)
            action = studio.show(output, fps, background is not None, hidden,
                                 max(0, capture_at-now) if capture_at else 0,
                                 capture_at is not None,
                                 worker.status if worker else 'Button and keyboard controls are ready',
                                 worker.progress if worker else 0)
            if studio.closed:
                break
            if action == 'b':
                capture_at = now + 5
                samples = []
                hidden = False
            if action == ' ' and background is not None and capture_at is None:
                hidden = not hidden
    finally:
        if recorder:
            recorder.close()
            print(f'Saved recording: {recorder.path}')
        if 'reader' in locals():
            reader.stop.set()
            reader.join(timeout=2)
        cap.release()
        if 'studio' in locals():
            studio.root.destroy()
        if worker:
            worker.stop.set()
            worker.join(timeout=3)
            if worker.error:
                print(f'Hand detection error: {worker.error}')


if __name__ == '__main__':
    main()

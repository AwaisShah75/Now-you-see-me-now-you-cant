"""Bounded, real-time MP4 recording without blocking the preview."""
from datetime import datetime
from pathlib import Path
import threading
import time

import cv2


class Recorder(threading.Thread):
    def __init__(self, folder):
        super().__init__(daemon=True)
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / (datetime.now().strftime('session_%Y-%m-%d_%H-%M-%S_%f') + '.mp4')
        self.writer = cv2.VideoWriter(str(self.path), cv2.VideoWriter_fourcc(*'mp4v'), 30, (1280, 720))
        if not self.writer.isOpened():
            self.writer.release()
            raise RuntimeError('Cannot create MP4 recording. Check available disk space and folder access.')
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.latest = None
        self.error = None
        self.frames_written = 0

    def submit(self, frame):
        # The caller never mutates output after submitting it.
        with self.lock:
            self.latest = frame

    def run(self):
        deadline = None
        try:
            while not self.stop.is_set():
                with self.lock:
                    frame = self.latest
                if frame is None:
                    self.stop.wait(.01)
                    continue
                if deadline is None:
                    deadline = time.perf_counter()
                # Duplicate the latest frame when capture is slower than 30 FPS,
                # keeping playback duration aligned with real elapsed time.
                scale = min(1280/frame.shape[1], 720/frame.shape[0])
                width, height = int(frame.shape[1]*scale), int(frame.shape[0]*scale)
                if (width, height) != (frame.shape[1], frame.shape[0]):
                    frame = cv2.resize(frame, (width, height))
                frame = cv2.copyMakeBorder(frame, (720-height)//2, 720-height-(720-height)//2,
                                          (1280-width)//2, 1280-width-(1280-width)//2,
                                          cv2.BORDER_CONSTANT, value=(0, 0, 0))
                self.writer.write(frame)
                self.frames_written += 1
                deadline += 1/30
                self.stop.wait(max(0, deadline-time.perf_counter()))
        except Exception as exc:
            self.error = str(exc)
        finally:
            self.writer.release()

    def close(self):
        self.stop.set()
        self.join()
        if self.frames_written == 0:
            self.path.unlink(missing_ok=True)

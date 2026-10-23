"""Minimal desktop shell with a large, unobstructed camera view."""
import tkinter as tk
from PIL import Image, ImageTk
import cv2


class Studio:
    BG = '#0c1018'
    TEXT = '#edf2fa'
    MUTED = '#8c9bb1'
    ACCENT = '#a8efd3'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Now You See Me')
        self.root.configure(bg=self.BG)
        self.root.geometry('1120x800')
        self.root.minsize(760, 560)
        self.action = None
        self.closed = False
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.root.bind('<KeyPress>', self.key)
        header = tk.Frame(self.root, bg=self.BG)
        header.pack(fill='x', padx=20, pady=12)
        self.label(header, 'Now you see me.', 16, self.TEXT).pack(side='left')
        self.fps = self.label(header, '', 10, self.ACCENT)
        self.fps.pack(side='right')
        # Fixed allocation avoids the image's requested size growing the window.
        viewport = tk.Frame(self.root, bg='#05080d')
        viewport.pack(fill='both', expand=True, padx=12)
        viewport.pack_propagate(False)
        self.video = tk.Label(viewport, bg='#05080d', bd=0)
        self.video.pack(fill='both', expand=True)
        controls = tk.Frame(self.root, bg=self.BG)
        controls.pack(fill='x', padx=20, pady=(12, 5))
        self.capture = self.button(controls, 'Capture background', 'b', self.ACCENT, '#10251e')
        self.capture.pack(side='left')
        self.toggle = self.button(controls, 'Vanish', ' ', '#263448', self.TEXT)
        self.toggle.pack(side='left', padx=10)
        self.state = self.label(controls, '', 11, self.TEXT)
        self.state.pack(side='left', padx=12)
        self.gesture = self.label(self.root, '', 10, self.MUTED)
        self.gesture.pack(anchor='w', padx=20, pady=(0, 12))
        self.root.update()

    def label(self, parent, text, size, color):
        return tk.Label(parent, text=text, font=('Segoe UI', size), fg=color, bg=self.BG)

    def button(self, parent, text, action, bg, fg):
        return tk.Button(parent, text=text, command=lambda: self.choose(action),
                         font=('Segoe UI', 11, 'bold'), bg=bg, fg=fg, bd=0,
                         activebackground=bg, activeforeground=fg, cursor='hand2',
                         padx=20, pady=10, disabledforeground='#66758a')

    def choose(self, action):
        self.action = action

    def key(self, event):
        if event.keysym == 'Escape' or event.char.lower() == 'q':
            self.close()
        elif event.char.lower() in ('b', ' '):
            self.choose(event.char.lower())

    def close(self):
        self.closed = True

    def set_text(self, widget, text):
        if widget.cget('text') != text:
            widget.configure(text=text)

    def show(self, frame, fps, ready, hidden, remaining, capturing, status, progress):
        width = max(1, self.video.winfo_width())
        height = max(1, self.video.winfo_height())
        scale = min(width/frame.shape[1], height/frame.shape[0])
        size = (max(1, int(frame.shape[1]*scale)), max(1, int(frame.shape[0]*scale)))
        rgb = cv2.cvtColor(cv2.resize(frame, size), cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)
        if hasattr(self, 'photo') and self.photo.width() == size[0] and self.photo.height() == size[1]:
            self.photo.paste(image)
        else:
            self.photo = ImageTk.PhotoImage(image)
            self.video.configure(image=self.photo)
        self.set_text(self.fps, f'{fps:.0f} FPS')
        if capturing:
            text = f'Step out of view  /  {remaining:.0f}s' if remaining > 0 else 'Capturing background...'
        elif not ready:
            text = 'Capture the empty room first.'
        else:
            text = 'Hidden' if hidden else 'Live'
        self.set_text(self.state, text)
        self.capture.configure(state='disabled' if capturing else 'normal')
        self.toggle.configure(text='Reappear' if hidden else 'Vanish',
                              state='normal' if ready and not capturing else 'disabled')
        self.set_text(self.gesture, status if 'Loading' in status or 'unavailable' in status else
                      'Close your fist briefly to toggle. Open your hand to reset.   |   Space: toggle')
        self.root.update_idletasks()
        self.root.update()
        action, self.action = self.action, None
        return action

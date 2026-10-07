"""Keyboard, mouse and volume control on the host PC."""

import logging
import shutil
import subprocess
import sys

log = logging.getLogger(__name__)


class Actions:
    """Thin wrapper over pynput. Backends are created lazily so the server
    still starts (and reports the error) on systems without input access."""

    def __init__(self):
        self._kb = None
        self._mouse = None
        self._keys = None
        self._buttons = None
        self.error = None
        try:
            from pynput import keyboard, mouse

            self._kb = keyboard.Controller()
            self._mouse = mouse.Controller()
            self._keys = keyboard.Key
            self._buttons = mouse.Button
        except Exception as e:  # no display, missing permissions, etc.
            self.error = str(e)
            log.error("No se pudo inicializar el control de teclado/mouse: %s", e)

    @property
    def ok(self):
        return self._kb is not None

    # --- keyboard -----------------------------------------------------------

    def _named_keys(self):
        K = self._keys
        return {
            "next": K.right,
            "prev": K.left,
            # Fullscreen slideshow from the current slide (PowerPoint, LibreOffice).
            "present": (K.cmd, K.enter) if sys.platform == "darwin" else (K.shift, K.f5),
            "start": K.f5,
            "end": K.esc,
            "esc": K.esc,
            "enter": K.enter,
            "backspace": K.backspace,
            "tab": K.tab,
            "space": K.space,
        }

    def key(self, name):
        if not self.ok:
            return
        key = self._named_keys().get(name)
        if key is None:
            log.warning("Tecla desconocida: %s", name)
            return
        if isinstance(key, tuple):
            *modifiers, last = key
            with self._kb.pressed(*modifiers):
                self._kb.tap(last)
        else:
            self._kb.tap(key)

    def type_text(self, text):
        if self.ok and text:
            self._kb.type(text)

    # --- mouse --------------------------------------------------------------

    def mouse_move(self, dx, dy):
        if self.ok:
            self._mouse.move(int(dx), int(dy))

    def click(self, button):
        if self.ok:
            b = self._buttons.right if button == "right" else self._buttons.left
            self._mouse.click(b)

    def scroll(self, dy):
        if self.ok:
            self._mouse.scroll(0, int(dy))

    # --- volume -------------------------------------------------------------

    def volume(self, action):
        # Linux desktops don't always react to media keys, pactl is more reliable.
        if sys.platform.startswith("linux") and shutil.which("pactl"):
            args = {
                "up": ["set-sink-volume", "@DEFAULT_SINK@", "+5%"],
                "down": ["set-sink-volume", "@DEFAULT_SINK@", "-5%"],
                "mute": ["set-sink-mute", "@DEFAULT_SINK@", "toggle"],
            }.get(action)
            if args:
                subprocess.run(["pactl", *args], check=False)
            return
        if not self.ok:
            return
        K = self._keys
        key = {
            "up": K.media_volume_up,
            "down": K.media_volume_down,
            "mute": K.media_volume_mute,
        }.get(action)
        if key is not None:
            self._kb.tap(key)

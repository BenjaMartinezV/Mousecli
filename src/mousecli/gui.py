"""Qt GUI: transparent click-through laser overlay + small window with the QR.

The server runs in another thread and only touches `LaserState` (lock-guarded).
All Qt objects live in the GUI thread and poll that state on a 60 Hz timer.
"""

import threading
from collections import deque

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QFont, QGuiApplication, QPainter, QRadialGradient
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget

FRAME_MS = 16
TRAIL_LEN = 10


class LaserState:
    """Thread-safe mailbox between the server thread and the overlay."""

    def __init__(self):
        self._lock = threading.Lock()
        self._active = False
        self._dx = 0.0
        self._dy = 0.0
        self._size = 14.0
        self._screen_step = 0
        self.screen_names = []

    def move(self, dx, dy):
        with self._lock:
            self._dx += dx
            self._dy += dy

    def set_active(self, on):
        with self._lock:
            self._active = on

    def set_size(self, size):
        with self._lock:
            self._size = max(4.0, min(60.0, size))

    def next_screen(self):
        with self._lock:
            self._screen_step += 1
            names = self.screen_names
            return names[self._screen_step % len(names)] if names else ""

    def take(self):
        with self._lock:
            d = (self._dx, self._dy)
            self._dx = self._dy = 0.0
            return self._active, d, self._size, self._screen_step


class LaserOverlay(QWidget):
    def __init__(self, state: LaserState):
        super().__init__(None)
        self.state = state
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.target = QPointF()
        self.pos_ = QPointF()
        self.trail = deque(maxlen=TRAIL_LEN)
        self.alpha = 0.0
        self.size = 14.0
        self.screen_step = None
        self.base_screen = 0

        screens = QGuiApplication.screens()
        primary = QGuiApplication.primaryScreen()
        # A projector is usually the secondary (extended) display.
        for i, s in enumerate(screens):
            if s is not primary:
                self.base_screen = i
                break
        self._refresh_screen_names()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(FRAME_MS)

    def _refresh_screen_names(self):
        screens = QGuiApplication.screens()
        n = len(screens)
        # Ordered starting from the default screen so step 0 == default.
        self.state.screen_names = [
            f"{screens[(self.base_screen + i) % n].name() or 'Pantalla'} ({i + 1}/{n})" for i in range(n)
        ]

    def _apply_screen(self, step):
        screens = QGuiApplication.screens()
        screen = screens[(self.base_screen + step) % len(screens)]
        self.setGeometry(screen.geometry())
        self.target = QPointF(self.width() / 2, self.height() / 2)
        self.pos_ = QPointF(self.target)
        self.trail.clear()

    def tick(self):
        active, (dx, dy), self.size, step = self.state.take()
        if step != self.screen_step:
            self.screen_step = step
            self._refresh_screen_names()
            self._apply_screen(step)

        if active and self.alpha == 0.0:
            # Fresh activation: show without stealing focus from the slideshow.
            self.trail.clear()
            self.show()
            self.raise_()

        if active:
            self.alpha = min(1.0, self.alpha + 0.25)
        elif self.alpha > 0:
            self.alpha = max(0.0, self.alpha - 0.08)
            if self.alpha == 0.0:
                self.hide()
                return
        else:
            return

        self.target.setX(max(0.0, min(self.width() - 1.0, self.target.x() + dx)))
        self.target.setY(max(0.0, min(self.height() - 1.0, self.target.y() + dy)))
        # Light smoothing hides network jitter without adding noticeable delay.
        self.pos_ += (self.target - self.pos_) * 0.6
        self.trail.append(QPointF(self.pos_))
        self.update()

    def paintEvent(self, event):
        if not self.trail:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        n = len(self.trail)
        for i, pt in enumerate(self.trail):
            k = (i + 1) / n
            if i < n - 1:
                p.setBrush(QColor(255, 40, 40, int(90 * k * k * self.alpha)))
                r = self.size * 0.5 * k
                p.drawEllipse(pt, r, r)
        head = self.trail[-1]
        r = self.size * 2.2
        g = QRadialGradient(head, r)
        a = self.alpha
        g.setColorAt(0.0, QColor(255, 255, 255, int(255 * a)))
        g.setColorAt(0.12, QColor(255, 60, 60, int(255 * a)))
        g.setColorAt(0.35, QColor(255, 20, 20, int(150 * a)))
        g.setColorAt(1.0, QColor(255, 0, 0, 0))
        p.setBrush(QBrush(g))
        p.drawEllipse(head, r, r)
        p.end()


class QrWidget(QWidget):
    def __init__(self, matrix):
        super().__init__()
        self.matrix = matrix
        self.setFixedSize(260, 260)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("white"))
        n = len(self.matrix)
        cell = self.width() / n
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("black"))
        for y, row in enumerate(self.matrix):
            for x, on in enumerate(row):
                if on:
                    p.drawRect(QRectF(x * cell, y * cell, cell + 0.5, cell + 0.5))
        p.end()


class MainWindow(QWidget):
    def __init__(self, url, qr_matrix, server):
        super().__init__()
        self.server = server
        self.setWindowTitle("Mousecli")
        self.setStyleSheet(
            "QWidget { background: #111318; color: #e8e8ee; }"
            "QPushButton { background: #23262f; border: 1px solid #333846;"
            " border-radius: 8px; padding: 8px 16px; }"
            "QPushButton:hover { background: #2c3040; }"
        )
        title = QLabel("Mousecli")
        title.setFont(QFont(title.font().family(), 18, QFont.Weight.Bold))
        hint = QLabel("Escanea el QR con tu teléfono")
        url_lbl = QLabel(url)
        url_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        url_lbl.setStyleSheet("color: #8b90a0; font-size: 11px;")
        self.status = QLabel()
        tip = QLabel("Teléfono y PC deben estar en la misma red WiFi.\n¿No conecta? Usa el hotspot del teléfono.")
        tip.setStyleSheet("color: #8b90a0; font-size: 11px;")
        quit_btn = QPushButton("Salir")
        quit_btn.clicked.connect(QApplication.quit)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(10)
        for w in (title, hint):
            lay.addWidget(w, alignment=Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(QrWidget(qr_matrix), alignment=Qt.AlignmentFlag.AlignHCenter)
        for w in (url_lbl, self.status, tip, quit_btn):
            lay.addWidget(w, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(500)
        self.refresh()

    def refresh(self):
        n = self.server.clients
        if n:
            self.status.setText(f"● {n} teléfono{'s' if n > 1 else ''} conectado{'s' if n > 1 else ''}")
            self.status.setStyleSheet("color: #4ade80;")
        else:
            self.status.setText("○ Esperando conexión…")
            self.status.setStyleSheet("color: #fbbf24;")

    def closeEvent(self, event):
        QApplication.quit()

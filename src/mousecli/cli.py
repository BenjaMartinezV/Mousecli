import argparse
import logging
import os
import secrets
import signal
import socket
import sys
import threading
from pathlib import Path

import qrcode

from . import __version__
from . import server as srv
from .actions import Actions

log = logging.getLogger("mousecli")


def config_dir():
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
        return base / "Mousecli"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Mousecli"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "mousecli"


def load_token(regenerate=False):
    """Token persists between runs so a saved phone shortcut keeps working."""
    path = config_dir() / "token"
    if not regenerate and path.exists():
        token = path.read_text().strip()
        if token:
            return token
    token = secrets.token_urlsafe(9)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token)
    return token


def lan_ip():
    # Connecting a UDP socket sends nothing; it just picks the outgoing interface.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"


def print_qr(url):
    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.make(fit=True)
    try:
        qr.print_ascii(invert=True)
    except UnicodeEncodeError:  # legacy Windows consoles
        pass


def start_server_thread(server, host, port):
    ready = threading.Event()
    error = []

    def target():
        try:
            srv.run(server, host, port, loop_ready=ready.set)
        except Exception as e:
            error.append(e)
            ready.set()

    threading.Thread(target=target, daemon=True, name="mousecli-server").start()
    ready.wait()
    if error:
        raise error[0]


def setup_logging(verbose):
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s %(message)s"
    if sys.stderr is None:
        # Windowed build (no console): log to a file instead.
        path = config_dir() / "mousecli.log"
        path.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(filename=path, filemode="w", encoding="utf-8", level=level, format=fmt, datefmt="%H:%M:%S")
    else:
        logging.basicConfig(level=level, format=fmt, datefmt="%H:%M:%S")


def set_windows_app_id():
    # Without this, Windows groups the window under python.exe and shows its icon.
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Mousecli.Mousecli")
        except Exception:
            pass


def main(argv=None):
    p = argparse.ArgumentParser(prog="mousecli", description="Control de presentaciones desde el teléfono.")
    p.add_argument("--port", type=int, default=8765, help="puerto (default: 8765)")
    p.add_argument("--host", help="IP a mostrar en el QR (default: autodetectada)")
    p.add_argument("--no-gui", action="store_true", help="sin ventana ni puntero láser (solo terminal)")
    p.add_argument("--new-token", action="store_true", help="generar un token nuevo (desconecta teléfonos guardados)")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--version", action="version", version=f"mousecli {__version__}")
    args = p.parse_args(argv)

    setup_logging(args.verbose)
    token = load_token(args.new_token)
    url = f"http://{args.host or lan_ip()}:{args.port}/?token={token}"
    actions = Actions()

    use_gui = not args.no_gui
    if use_gui:
        try:
            from PyQt6.QtCore import QTimer
            from PyQt6.QtGui import QIcon
            from PyQt6.QtWidgets import QApplication, QMessageBox

            from . import gui
        except ImportError as e:
            log.warning("PyQt6 no disponible (%s): el puntero láser queda desactivado.", e)
            use_gui = False

    laser = gui.LaserState() if use_gui else None
    server = srv.Server(actions, token, overlay=laser)

    if sys.stdout is not None:
        print(f"\n  Mousecli {__version__}\n  Abre en tu teléfono: {url}\n")
        print_qr(url)
        print("  Teléfono y PC deben estar en la misma red (o usa el hotspot del teléfono).")
        print("  Ctrl+C para salir.\n")
    log.info("URL: %s", url)

    if not use_gui:
        try:
            srv.run(server, "0.0.0.0", args.port)
        except KeyboardInterrupt:
            pass
        return

    set_windows_app_id()
    if sys.platform == "darwin":
        # By default Qt activates the whole app when a window is raised.
        os.environ.setdefault("QT_MAC_SET_RAISE_PROCESS", "0")
    app = QApplication(sys.argv)
    app.setApplicationName("Mousecli")
    app.setWindowIcon(QIcon(str(srv.WEB_DIR / "icon-512.png")))

    try:
        start_server_thread(server, "0.0.0.0", args.port)
    except OSError as e:
        log.error("No se pudo abrir el puerto %d: %s", args.port, e)
        QMessageBox.critical(
            None,
            "Mousecli",
            f"No se pudo abrir el puerto {args.port}.\n\n"
            "Probablemente Mousecli ya está abierto. Revisa la barra de tareas.",
        )
        sys.exit(1)

    qr = qrcode.QRCode(border=2)
    qr.add_data(url)
    qr.make(fit=True)
    window = gui.MainWindow(url, qr.get_matrix(), server)
    window.show()
    overlay = gui.LaserOverlay(laser)  # noqa: F841 (kept alive by reference)
    if sys.platform == "darwin":
        from . import macos

        macos.make_accessory_app()

    # Let Ctrl+C in the terminal close the Qt app.
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    keepalive = QTimer()
    keepalive.timeout.connect(lambda: None)
    keepalive.start(250)

    sys.exit(app.exec())

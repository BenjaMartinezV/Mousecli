"""Regenerate the PNG and ICO icons from src/mousecli/web/icon.svg (needs PyQt6)."""

import struct
import sys
from pathlib import Path

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PyQt6.QtGui import QGuiApplication, QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "src" / "mousecli" / "web"
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


def render(svg, size):
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    QSvgRenderer(QByteArray(svg.encode())).render(p)
    p.end()
    return img


def png_bytes(img):
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buf, "PNG")
    return bytes(buf.data())


def write_ico(svg, path):
    """Multi-size ICO with PNG-encoded entries (supported since Windows Vista)."""
    images = [png_bytes(render(svg, s)) for s in ICO_SIZES]
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries = b""
    for size, data in zip(ICO_SIZES, images):
        dim = 0 if size >= 256 else size  # 0 means 256 in the ICO format
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    path.write_bytes(header + entries + b"".join(images))


def main():
    QGuiApplication(sys.argv[:1] + ["-platform", "offscreen"])
    svg = (WEB / "icon.svg").read_text()
    render(svg, 192).save(str(WEB / "icon-192.png"))
    render(svg, 512).save(str(WEB / "icon-512.png"))
    # iOS applies its own rounded mask, so this one is full-bleed.
    render(svg.replace('rx="224"', 'rx="0"', 1), 180).save(str(WEB / "apple-touch-icon.png"))
    (ROOT / "assets").mkdir(exist_ok=True)
    write_ico(svg, ROOT / "assets" / "icon.ico")
    print("Iconos generados.")


if __name__ == "__main__":
    main()

"""Build the standalone app for the current OS and pack it into dist/*.zip.

Usage:  pip install . pyinstaller pillow
        python scripts/build.py
"""

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from mousecli import __version__  # noqa: E402

NAME = "Mousecli"
DIST = ROOT / "dist"
BUILD = ROOT / "build"


def pyinstaller(*extra):
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name",
        NAME,
        "--windowed",  # no console window
        "--collect-data",
        "mousecli",
        "--distpath",
        str(DIST),
        "--workpath",
        str(BUILD),
        "--specpath",
        str(BUILD),
        *extra,
        str(ROOT / "src" / "mousecli" / "__main__.py"),
    ]
    subprocess.run(cmd, check=True)


def zip_file(src, dest, arcname):
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        info = zipfile.ZipInfo.from_file(src, arcname)
        info.external_attr = 0o755 << 16  # keep it executable on Linux
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, Path(src).read_bytes())


def main():
    shutil.rmtree(DIST, ignore_errors=True)
    tag = f"{NAME}-v{__version__}"

    if sys.platform == "win32":
        pyinstaller("--onefile", "--icon", str(ROOT / "assets" / "icon.ico"))
        out = DIST / f"{tag}-windows.zip"
        zip_file(DIST / f"{NAME}.exe", out, f"{NAME}.exe")
    elif sys.platform == "darwin":
        # PyInstaller converts the PNG to .icns using Pillow.
        pyinstaller(
            "--onedir",
            "--icon",
            str(ROOT / "src" / "mousecli" / "web" / "icon-512.png"),
            "--osx-bundle-identifier",
            "io.github.benjamartinezv.mousecli",
        )
        out = DIST / f"{tag}-macos.zip"
        # ditto keeps the symlinks and permissions a .app bundle needs.
        subprocess.run(["ditto", "-c", "-k", "--keepParent", str(DIST / f"{NAME}.app"), str(out)], check=True)
    else:
        pyinstaller("--onefile")
        out = DIST / f"{tag}-linux.zip"
        zip_file(DIST / NAME, out, NAME)

    print(f"\nListo: {out}")


if __name__ == "__main__":
    main()

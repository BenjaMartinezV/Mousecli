"""macOS tweaks through the Objective-C runtime (ctypes, no extra dependencies).

Without them, showing the laser activates Mousecli, which makes macOS leave
PowerPoint's fullscreen slideshow and jump back to the desktop.
"""

import ctypes
import ctypes.util
import logging

log = logging.getLogger(__name__)

NS_ACTIVATION_POLICY_ACCESSORY = 1
NS_SCREEN_SAVER_WINDOW_LEVEL = 1000
# canJoinAllSpaces | stationary | ignoresCycle | fullScreenAuxiliary
OVERLAY_COLLECTION_BEHAVIOR = (1 << 0) | (1 << 4) | (1 << 6) | (1 << 8)

_objc = None


def _runtime():
    global _objc
    if _objc is None:
        ctypes.cdll.LoadLibrary(ctypes.util.find_library("AppKit"))
        objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
        objc.objc_getClass.restype = ctypes.c_void_p
        objc.objc_getClass.argtypes = [ctypes.c_char_p]
        objc.sel_registerName.restype = ctypes.c_void_p
        objc.sel_registerName.argtypes = [ctypes.c_char_p]
        _objc = objc
    return _objc


def _send(obj, selector, *args, restype=ctypes.c_void_p, argtypes=()):
    # objc_msgSend must be called through a prototype that matches each method
    # (it is not variadic on Apple Silicon).
    objc = _runtime()
    address = ctypes.cast(objc.objc_msgSend, ctypes.c_void_p).value
    fn = ctypes.CFUNCTYPE(restype, ctypes.c_void_p, ctypes.c_void_p, *argtypes)(address)
    return fn(obj, objc.sel_registerName(selector.encode()), *args)


def _shared_app():
    return _send(_runtime().objc_getClass(b"NSApplication"), "sharedApplication")


def make_accessory_app():
    """No Dock icon and never steal focus: required to float over another app's fullscreen Space."""
    try:
        app = _shared_app()
        _send(
            app, "setActivationPolicy:", NS_ACTIVATION_POLICY_ACCESSORY, restype=ctypes.c_bool, argtypes=[ctypes.c_long]
        )
        # Bring the QR window to the front once at launch.
        _send(app, "activateIgnoringOtherApps:", True, restype=None, argtypes=[ctypes.c_bool])
    except Exception:
        log.exception("No se pudo configurar la app como accesorio de macOS")


def configure_overlay(win_id):
    """Show the overlay on every Space, fullscreen slideshows included, above everything."""
    try:
        window = _send(ctypes.c_void_p(int(win_id)), "window")
        if not window:
            return
        _send(
            window,
            "setCollectionBehavior:",
            OVERLAY_COLLECTION_BEHAVIOR,
            restype=None,
            argtypes=[ctypes.c_ulong],
        )
        _send(window, "setLevel:", NS_SCREEN_SAVER_WINDOW_LEVEL, restype=None, argtypes=[ctypes.c_long])
        _send(window, "setHidesOnDeactivate:", False, restype=None, argtypes=[ctypes.c_bool])
    except Exception:
        log.exception("No se pudo configurar la capa del láser en macOS")

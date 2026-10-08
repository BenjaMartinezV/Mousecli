"""HTTP + WebSocket server: serves the phone web app and dispatches commands."""

import asyncio
import hmac
import json
import logging
from pathlib import Path

from aiohttp import WSMsgType, web

from . import __version__

log = logging.getLogger(__name__)

WEB_DIR = Path(__file__).parent / "web"

# Plain HTTP commands for clients that can't hold a WebSocket open, such as
# Apple Shortcuts on the iPhone or Apple Watch ("Get Contents of URL").
API_COMMANDS = {
    "next": {"t": "key", "k": "next"},
    "prev": {"t": "key", "k": "prev"},
    "present": {"t": "key", "k": "present"},
    "end": {"t": "key", "k": "end"},
    "volume-up": {"t": "vol", "a": "up"},
    "volume-down": {"t": "vol", "a": "down"},
    "mute": {"t": "vol", "a": "mute"},
}


class Server:
    def __init__(self, actions, token, overlay=None):
        self.actions = actions
        self.token = token
        self.overlay = overlay
        self.clients = 0

    def app(self):
        app = web.Application()
        app.router.add_get("/ws", self.ws_handler)
        # HEAD must never trigger an action, so it is not routed.
        app.router.add_get("/api/{cmd}", self.api_handler, allow_head=False)
        app.router.add_post("/api/{cmd}", self.api_handler)
        app.router.add_get("/", self.index)
        app.router.add_static("/", WEB_DIR)
        return app

    async def index(self, request):
        return web.FileResponse(WEB_DIR / "index.html", headers={"Cache-Control": "no-cache"})

    def _authorized(self, request):
        return hmac.compare_digest(request.query.get("token", ""), self.token)

    async def api_handler(self, request):
        if not self._authorized(request):
            log.warning("Comando HTTP rechazado (token inválido) desde %s", request.remote)
            raise web.HTTPForbidden()
        cmd = request.match_info["cmd"]
        msg = API_COMMANDS.get(cmd)
        if msg is None:
            return web.json_response(
                {"ok": False, "error": "comando desconocido", "commands": list(API_COMMANDS)}, status=404
            )
        await self.dispatch(msg)
        return web.json_response({"ok": True, "command": cmd})

    async def ws_handler(self, request):
        if not self._authorized(request):
            log.warning("Conexión rechazada (token inválido) desde %s", request.remote)
            raise web.HTTPForbidden()

        ws = web.WebSocketResponse(heartbeat=10, compress=False)
        await ws.prepare(request)
        self.clients += 1
        log.info("Teléfono conectado desde %s", request.remote)

        await ws.send_json(
            {
                "t": "hello",
                "version": __version__,
                "input": self.actions.ok,
                "laser": self.overlay is not None,
            }
        )
        try:
            async for msg in ws:
                if msg.type != WSMsgType.TEXT:
                    continue
                try:
                    data = json.loads(msg.data)
                    reply = await self.dispatch(data)
                    if reply is not None:
                        await ws.send_json(reply)
                except Exception:
                    log.exception("Error procesando mensaje: %r", msg.data)
        finally:
            self.clients -= 1
            if self.overlay:
                # Never leave the laser stuck on screen if the phone drops.
                self.overlay.set_active(False)
            log.info("Teléfono desconectado (%s)", request.remote)
        return ws

    async def dispatch(self, d):
        t = d.get("t")
        a = self.actions
        if t == "lm" and self.overlay:
            self.overlay.move(float(d.get("x", 0)), float(d.get("y", 0)))
        elif t == "mm":
            a.mouse_move(d.get("x", 0), d.get("y", 0))
        elif t == "laser" and self.overlay:
            self.overlay.set_active(bool(d.get("on")))
        elif t == "key":
            a.key(d.get("k"))
        elif t == "click":
            a.click(d.get("b", "left"))
        elif t == "scroll":
            a.scroll(d.get("y", 0))
        elif t == "vol":
            a.volume(d.get("a"))
        elif t == "type":
            # Typing long text is slow; don't block the event loop.
            await asyncio.get_running_loop().run_in_executor(None, a.type_text, str(d.get("s", "")))
        elif t == "cfg" and self.overlay:
            if "size" in d:
                self.overlay.set_size(float(d["size"]))
            if d.get("screen") == "next":
                return {"t": "screen", "name": self.overlay.next_screen()}
        elif t == "ping":
            return {"t": "pong", "id": d.get("id")}
        return None


def run(server, host, port, loop_ready=None):
    """Run the server forever in the current thread (creates its own loop)."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    runner = web.AppRunner(server.app(), access_log=None)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, host, port)
    loop.run_until_complete(site.start())
    if loop_ready:
        loop_ready()
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(runner.cleanup())

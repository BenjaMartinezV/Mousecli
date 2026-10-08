import pytest
from aiohttp import WSServerHandshakeError

from mousecli.server import Server

TOKEN = "secret"


class FakeActions:
    ok = True

    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        return lambda *args: self.calls.append((name, *args))


class FakeOverlay:
    def __init__(self):
        self.active = False
        self.moves = []

    def move(self, dx, dy):
        self.moves.append((dx, dy))

    def set_active(self, on):
        self.active = on

    def set_size(self, size):
        pass

    def next_screen(self):
        return "Pantalla (2/2)"


@pytest.fixture
def actions():
    return FakeActions()


@pytest.fixture
def overlay():
    return FakeOverlay()


@pytest.fixture
async def ws(aiohttp_client, actions, overlay):
    client = await aiohttp_client(Server(actions, TOKEN, overlay=overlay).app())
    async with client.ws_connect(f"/ws?token={TOKEN}") as ws:
        hello = await ws.receive_json()
        assert hello["t"] == "hello"
        yield ws


async def test_serves_web_app(aiohttp_client, actions):
    client = await aiohttp_client(Server(actions, TOKEN).app())
    for path in ("/", "/app.js", "/style.css", "/manifest.json", "/icon.svg"):
        resp = await client.get(path)
        assert resp.status == 200, path


async def test_rejects_invalid_token(aiohttp_client, actions):
    client = await aiohttp_client(Server(actions, TOKEN).app())
    with pytest.raises(WSServerHandshakeError) as exc:
        await client.ws_connect("/ws?token=wrong")
    assert exc.value.status == 403


async def test_hello_reports_capabilities(aiohttp_client, actions):
    client = await aiohttp_client(Server(actions, TOKEN).app())
    async with client.ws_connect(f"/ws?token={TOKEN}") as ws:
        hello = await ws.receive_json()
    assert hello["input"] is True
    assert hello["laser"] is False


async def test_ping_pong(ws):
    await ws.send_json({"t": "ping", "id": 42})
    assert await ws.receive_json() == {"t": "pong", "id": 42}


async def test_input_commands(ws, actions):
    for msg in (
        {"t": "key", "k": "next"},
        {"t": "key", "k": "present"},
        {"t": "key", "k": "end"},
        {"t": "vol", "a": "up"},
        {"t": "mm", "x": 3, "y": -2},
        {"t": "click", "b": "right"},
        {"t": "scroll", "y": -1},
        {"t": "type", "s": "hola ñandú"},
    ):
        await ws.send_json(msg)
    await ws.send_json({"t": "ping", "id": 0})  # barrier: replies arrive in order
    await ws.receive_json()
    assert actions.calls == [
        ("key", "next"),
        ("key", "present"),
        ("key", "end"),
        ("volume", "up"),
        ("mouse_move", 3, -2),
        ("click", "right"),
        ("scroll", -1),
        ("type_text", "hola ñandú"),
    ]


async def test_laser(ws, overlay):
    await ws.send_json({"t": "laser", "on": True})
    await ws.send_json({"t": "lm", "x": 1.5, "y": -2})
    await ws.send_json({"t": "cfg", "screen": "next"})
    assert await ws.receive_json() == {"t": "screen", "name": "Pantalla (2/2)"}
    assert overlay.active is True
    assert overlay.moves == [(1.5, -2.0)]


async def test_disconnect_resets_overlay(aiohttp_client, actions, overlay):
    client = await aiohttp_client(Server(actions, TOKEN, overlay=overlay).app())
    async with client.ws_connect(f"/ws?token={TOKEN}") as ws:
        await ws.receive_json()
        await ws.send_json({"t": "laser", "on": True})
        await ws.send_json({"t": "ping", "id": 0})
        await ws.receive_json()
        assert overlay.active is True
    await client.close()
    assert overlay.active is False


async def test_http_api_runs_command(aiohttp_client, actions):
    client = await aiohttp_client(Server(actions, TOKEN).app())
    resp = await client.get(f"/api/next?token={TOKEN}")
    assert resp.status == 200
    assert await resp.json() == {"ok": True, "command": "next"}
    resp = await client.post(f"/api/volume-up?token={TOKEN}")
    assert resp.status == 200
    assert actions.calls == [("key", "next"), ("volume", "up")]


async def test_http_api_rejects_invalid_token(aiohttp_client, actions):
    client = await aiohttp_client(Server(actions, TOKEN).app())
    for url in ("/api/next", "/api/next?token=wrong"):
        resp = await client.get(url)
        assert resp.status == 403
    assert actions.calls == []


async def test_http_api_unknown_command(aiohttp_client, actions):
    client = await aiohttp_client(Server(actions, TOKEN).app())
    resp = await client.get(f"/api/explode?token={TOKEN}")
    assert resp.status == 404
    assert "next" in (await resp.json())["commands"]
    assert actions.calls == []


async def test_http_api_head_does_nothing(aiohttp_client, actions):
    # Link previews and prefetchers send HEAD; it must never change a slide.
    client = await aiohttp_client(Server(actions, TOKEN).app())
    resp = await client.head(f"/api/next?token={TOKEN}")
    assert resp.status != 200
    assert actions.calls == []

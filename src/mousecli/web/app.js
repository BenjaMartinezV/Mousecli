"use strict";

const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

// --- settings ----------------------------------------------------------------

const DEFAULTS = { laserSens: 3, laserSize: 14, mouseSens: 1.5, haptics: true, mode: "laser" };
const settings = { ...DEFAULTS, ...load("mousecli.settings") };

function load(key) {
  try { return JSON.parse(localStorage.getItem(key)) || {}; } catch { return {}; }
}
function save(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch {}
}

function buzz(pattern) {
  if (navigator.vibrate) navigator.vibrate(pattern);
}
function tapFeedback() {
  if (settings.haptics) buzz(12);
}

// --- connection --------------------------------------------------------------

const token = new URLSearchParams(location.search).get("token") || load("mousecli.token").token || "";
if (token) save("mousecli.token", { token });

let ws = null;
let everOpened = false;
let retryDelay = 300;
let retryTimer = null;
let server = {};

function setStatus(state, text) {
  $("#status").dataset.state = state;
  $("#status-text").textContent = text;
  if (state !== "ok") $("#latency").textContent = "";
}

function connect() {
  clearTimeout(retryTimer);
  if (ws && ws.readyState <= 1) return;
  if (!token) {
    setStatus("error", "Falta el token: escanea el QR");
    return;
  }
  setStatus("connecting", "Conectando…");
  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws?token=${encodeURIComponent(token)}`);

  ws.onopen = () => {
    everOpened = true;
    retryDelay = 300;
    setStatus("ok", "Conectado");
    send({ t: "cfg", size: settings.laserSize });
    requestWakeLock();
  };
  ws.onmessage = (e) => {
    const m = JSON.parse(e.data);
    if (m.t === "pong") {
      $("#latency").textContent = `${Math.round(performance.now() - m.id)} ms`;
    } else if (m.t === "hello") {
      server = m;
      $("#about").textContent = `Mousecli ${m.version}`;
      if (!m.input) setStatus("error", "El PC no permite controlar teclado/mouse");
      updateHint();
    } else if (m.t === "screen") {
      $("#screen-name").textContent = m.name;
    }
  };
  ws.onclose = () => {
    setStatus(everOpened ? "connecting" : "error", everOpened ? "Reconectando…" : "No se pudo conectar");
    retryTimer = setTimeout(connect, retryDelay);
    retryDelay = Math.min(retryDelay * 2, 3000);
  };
}

function send(obj) {
  if (ws && ws.readyState === 1) ws.send(JSON.stringify(obj));
}

setInterval(() => send({ t: "ping", id: performance.now() }), 2000);

document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") {
    connect();
    requestWakeLock();
  } else {
    // Locking the phone or switching apps mid-touch swallows the pointerup.
    resetPad();
  }
});
window.addEventListener("blur", () => resetPad());

// Keeps the phone screen on. Only available on HTTPS, so it's best-effort.
async function requestWakeLock() {
  try { await navigator.wakeLock?.request("screen"); } catch {}
}

// --- buttons -----------------------------------------------------------------

function bindPress(el, action, repeat = false) {
  let delay, interval;
  const stop = () => {
    clearTimeout(delay);
    clearInterval(interval);
    el.classList.remove("pressed");
  };
  el.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    el.classList.add("pressed");
    tapFeedback();
    action();
    if (repeat) delay = setTimeout(() => (interval = setInterval(action, 120)), 400);
  });
  ["pointerup", "pointercancel", "pointerleave"].forEach((ev) => el.addEventListener(ev, stop));
}

$$("[data-key]").forEach((el) => bindPress(el, () => send({ t: "key", k: el.dataset.key })));

// One button toggles the fullscreen slideshow. The PC can't tell us if the user
// left it some other way, so a desync only costs one extra tap.
let presenting = false;
const presentBtn = $("#btn-present");
function setPresenting(on) {
  presenting = on;
  presentBtn.classList.toggle("on", on);
  presentBtn.setAttribute("aria-label", on ? "Salir de pantalla completa" : "Pantalla completa");
}
bindPress(presentBtn, () => {
  send({ t: "key", k: presenting ? "end" : "present" });
  setPresenting(!presenting);
});
// The Esc and F5 shortcuts in the text tab also change the slideshow state.
$('[data-key="esc"]').addEventListener("pointerdown", () => setPresenting(false));
$('[data-key="start"]').addEventListener("pointerdown", () => setPresenting(true));

// Block pinch/double-tap zoom everywhere. iOS ignores user-scalable=no,
// so its gesture events and multi-touch moves are cancelled explicitly.
["gesturestart", "gesturechange", "gestureend"].forEach((ev) =>
  document.addEventListener(ev, (e) => e.preventDefault(), { passive: false })
);
document.addEventListener("touchmove", (e) => {
  if (e.touches.length > 1) e.preventDefault();
}, { passive: false });
document.addEventListener("dblclick", (e) => e.preventDefault(), { passive: false });
$$("[data-vol]").forEach((el) =>
  bindPress(el, () => send({ t: "vol", a: el.dataset.vol }), el.dataset.vol !== "mute")
);

// --- modes -------------------------------------------------------------------

function setMode(mode) {
  settings.mode = mode;
  save("mousecli.settings", settings);
  $$(".tabs button").forEach((b) => b.classList.toggle("active", b.dataset.mode === mode));
  $("#pad").hidden = mode === "text";
  $("#text-panel").hidden = mode !== "text";
  updateHint();
  resetPad();
  resizePad();
}

function updateHint() {
  const hints = {
    laser: server.laser === false
      ? "Puntero láser no disponible en este PC (se ejecutó sin GUI)"
      : "Mantén presionado y mueve el dedo para usar el láser",
    mouse: "Desliza para mover · Toca: clic · 2 dedos: clic derecho / scroll",
  };
  $("#pad-hint").textContent = hints[settings.mode] || "";
}

$$(".tabs button").forEach((b) => b.addEventListener("click", () => setMode(b.dataset.mode)));

// --- pad: laser + touchpad -----------------------------------------------------

const pad = $("#pad");
const canvas = $("#pad-canvas");
const ctx = canvas.getContext("2d");
const pointers = new Map();
const acc = { lx: 0, ly: 0, mx: 0, my: 0, sy: 0 };
let flushQueued = false;
let gesture = null; // { t0, maxPointers, moved }
let glow = { x: 0, y: 0, k: 0 };
let drawQueued = false;

const SCROLL_STEP = 22; // px of finger travel per scroll notch
// Generous on purpose: a real fingertip drifts a few px and lingers a bit.
const TAP_MS = 300;
const TAP_SLOP = 12;

function queueFlush() {
  if (!flushQueued) {
    flushQueued = true;
    requestAnimationFrame(flush);
  }
}

// Sends at most once per frame, coalescing all movement since the last one.
function flush() {
  flushQueued = false;
  if (acc.lx || acc.ly) {
    send({ t: "lm", x: +acc.lx.toFixed(1), y: +acc.ly.toFixed(1) });
    acc.lx = acc.ly = 0;
  }
  const mx = Math.trunc(acc.mx), my = Math.trunc(acc.my);
  if (mx || my) {
    send({ t: "mm", x: mx, y: my });
    acc.mx -= mx;
    acc.my -= my;
  }
  const sy = Math.trunc(acc.sy / SCROLL_STEP);
  if (sy) {
    send({ t: "scroll", y: sy });
    acc.sy -= sy * SCROLL_STEP;
  }
}

// Forget every tracked finger. Without this, a finger whose pointerup never
// arrived stays "on the pad" forever and every later tap looks like a
// two-finger gesture, so single clicks silently stop working.
function resetPad() {
  if (pointers.size && settings.mode === "laser") send({ t: "laser", on: false });
  pointers.clear();
  gesture = null;
  acc.mx = acc.my = acc.sy = 0;
}

pad.addEventListener("pointerdown", (e) => {
  e.preventDefault();
  // The first finger of a new touch means nothing else is on the screen.
  if (e.isPrimary && pointers.size) resetPad();
  try {
    pad.setPointerCapture(e.pointerId);
  } catch {}
  pointers.set(e.pointerId, { x: e.clientX, y: e.clientY, sx: e.clientX, sy: e.clientY });
  if (pointers.size === 1) {
    gesture = { t0: performance.now(), maxPointers: 1, moved: false };
    if (settings.mode === "laser") {
      send({ t: "laser", on: true });
      buzz(8);
    }
  } else if (gesture) {
    gesture.maxPointers = Math.max(gesture.maxPointers, pointers.size);
  }
  setGlow(e);
});

pad.addEventListener("pointermove", (e) => {
  const p = pointers.get(e.pointerId);
  if (!p) return;
  const dx = e.clientX - p.x, dy = e.clientY - p.y;
  p.x = e.clientX;
  p.y = e.clientY;
  if (Math.hypot(p.x - p.sx, p.y - p.sy) > TAP_SLOP && gesture) gesture.moved = true;

  if (settings.mode === "laser") {
    if (pointers.size === 1) {
      acc.lx += dx * settings.laserSens;
      acc.ly += dy * settings.laserSens;
    }
  } else if (pointers.size === 1) {
    // Mild acceleration: slow moves stay precise, fast flicks cover the screen.
    const gain = settings.mouseSens * Math.min(3, 1 + Math.hypot(dx, dy) * 0.08);
    acc.mx += dx * gain;
    acc.my += dy * gain;
  } else if (pointers.size === 2) {
    acc.sy += dy / 2; // both fingers report, so halve
  }
  queueFlush();
  setGlow(e);
});

function endPointer(e) {
  if (!pointers.delete(e.pointerId)) return;
  if (pointers.size > 0) return;

  if (settings.mode === "laser") {
    send({ t: "laser", on: false });
  } else if (e.type === "pointerup" && gesture && !gesture.moved && performance.now() - gesture.t0 < TAP_MS) {
    send({ t: "click", b: gesture.maxPointers >= 2 ? "right" : "left" });
    buzz(10);
  }
  gesture = null;
  acc.sy = 0;
  queueDraw();
}
// Only a real pointerup can be a tap; cancel or lost capture just ends the gesture.
pad.addEventListener("pointerup", endPointer);
pad.addEventListener("pointercancel", endPointer);
pad.addEventListener("lostpointercapture", endPointer);

// Dot grid that lights up around the finger.
function setGlow(e) {
  const r = pad.getBoundingClientRect();
  glow.x = e.clientX - r.left;
  glow.y = e.clientY - r.top;
  glow.k = 1;
  queueDraw();
}

function queueDraw() {
  if (!drawQueued) {
    drawQueued = true;
    requestAnimationFrame(draw);
  }
}

function resizePad() {
  const dpr = window.devicePixelRatio || 1;
  canvas.width = pad.clientWidth * dpr;
  canvas.height = pad.clientHeight * dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  queueDraw();
}
window.addEventListener("resize", resizePad);

function draw() {
  drawQueued = false;
  const w = pad.clientWidth, h = pad.clientHeight;
  ctx.clearRect(0, 0, w, h);
  const gap = 18, R = 110;
  const rgb = settings.mode === "laser" ? "255,59,59" : "91,140,255";
  if (pointers.size === 0) glow.k *= 0.85;
  for (let y = gap / 2; y < h; y += gap) {
    for (let x = gap / 2; x < w; x += gap) {
      const d = Math.hypot(x - glow.x, y - glow.y);
      const k = d < R ? (1 - d / R) * glow.k : 0;
      ctx.fillStyle = k > 0.02 ? `rgba(${rgb},${0.25 + 0.75 * k})` : "#262a35";
      ctx.beginPath();
      ctx.arc(x, y, 1.4 + 2.6 * k, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  if (pointers.size === 0 && glow.k > 0.02) queueDraw();
}

// --- text / dictation ----------------------------------------------------------

function sendText() {
  const input = $("#text-input");
  const text = input.value;
  if (!text) return;
  send({ t: "type", s: text });
  if ($("#text-enter").checked) send({ t: "key", k: "enter" });
  input.value = "";
  tapFeedback();
}
$("#text-send").addEventListener("click", sendText);

// --- settings dialog -----------------------------------------------------------

$("#btn-settings").addEventListener("click", () => $("#settings").showModal());

["laserSens", "laserSize", "mouseSens"].forEach((id) => {
  const input = $("#" + id);
  const out = $(`output[data-for="${id}"]`);
  input.value = settings[id];
  out.textContent = settings[id];
  input.addEventListener("input", () => {
    settings[id] = +input.value;
    out.textContent = input.value;
    save("mousecli.settings", settings);
    if (id === "laserSize") send({ t: "cfg", size: settings.laserSize });
  });
});
$("#haptics").checked = settings.haptics;
$("#haptics").addEventListener("change", (e) => {
  settings.haptics = e.target.checked;
  save("mousecli.settings", settings);
});
$("#btn-screen").addEventListener("click", () => send({ t: "cfg", screen: "next" }));

// --- Apple Watch / Shortcuts ---------------------------------------------------

const API_COMMANDS = [
  ["next", "Siguiente diapositiva"],
  ["prev", "Diapositiva anterior"],
];

function apiUrl(cmd) {
  return `${location.protocol}//${location.host}/api/${cmd}?token=${encodeURIComponent(token)}`;
}

// navigator.clipboard needs HTTPS; the textarea trick works over plain HTTP.
function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.setAttribute("readonly", "");
  ta.style.position = "fixed";
  ta.style.opacity = "0";
  $("#settings").appendChild(ta);
  ta.select();
  ta.setSelectionRange(0, text.length);
  const ok = document.execCommand("copy");
  ta.remove();
  return ok ? Promise.resolve() : Promise.reject(new Error("copy failed"));
}

for (const [cmd, label] of API_COMMANDS) {
  const row = document.createElement("div");
  row.className = "api-row";
  const info = document.createElement("div");
  const name = document.createElement("b");
  name.textContent = label;
  const url = document.createElement("code");
  url.textContent = apiUrl(cmd);
  info.append(name, url);
  const btn = document.createElement("button");
  btn.textContent = "Copiar";
  btn.addEventListener("click", () => {
    copyText(apiUrl(cmd)).then(
      () => (btn.textContent = "Copiado"),
      () => (btn.textContent = "Mantén presionada la dirección")
    );
    setTimeout(() => (btn.textContent = "Copiar"), 1800);
  });
  row.append(info, btn);
  $("#api-list").appendChild(row);
}

// --- timer ---------------------------------------------------------------------

const timer = {
  mode: "down", minutes: 15, alerts: [5, 1],
  running: false, startedAt: 0, elapsedBefore: 0, fired: [],
  ...load("mousecli.timer"),
};

const elapsed = () => timer.elapsedBefore + (timer.running ? Date.now() - timer.startedAt : 0);
const remaining = () => timer.minutes * 60000 - elapsed();

function fmt(ms) {
  const neg = ms < 0;
  const s = Math.floor(Math.abs(ms) / 1000);
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
  const mm = h ? `${h}:${String(m).padStart(2, "0")}` : String(m).padStart(2, "0");
  return `${neg ? "-" : ""}${mm}:${String(sec).padStart(2, "0")}`;
}

function timerClass() {
  const rem = remaining();
  if (!timer.running && elapsed() === 0) return "";
  if (rem <= 0) return "over";
  const sorted = [...timer.alerts].sort((a, b) => a - b);
  if (sorted.length && rem <= sorted[0] * 60000) return "danger";
  if (sorted.length && rem <= sorted[sorted.length - 1] * 60000) return "warn";
  return "ok";
}

function timerAlert(strong) {
  buzz(strong ? [500, 200, 500, 200, 500] : [200, 100, 200]);
  document.body.classList.remove("flash");
  void document.body.offsetWidth; // restart animation
  document.body.classList.add("flash");
}

// Mark alerts that are already behind us so changing settings doesn't fire them.
function syncFired() {
  const rem = remaining();
  timer.fired = [...timer.alerts, 0].filter((a) => rem <= a * 60000);
}

function renderTimer() {
  const rem = remaining();
  if (timer.running) {
    for (const a of [...timer.alerts, 0]) {
      if (rem <= a * 60000 && !timer.fired.includes(a)) {
        timer.fired.push(a);
        timerAlert(a === 0);
        save("mousecli.timer", timer);
      }
    }
  }
  const text = timer.mode === "down" ? fmt(rem) : fmt(elapsed());
  const cls = timerClass();
  for (const el of [$("#btn-timer"), $("#timer-big")]) {
    el.textContent = text;
    el.className = el.id === "btn-timer" ? `timer-chip ${cls}` : `timer-big ${cls}`;
  }
  $("#t-toggle").textContent = timer.running ? "Pausar" : elapsed() ? "Continuar" : "Iniciar";
}

function saveTimer() {
  save("mousecli.timer", timer);
  renderTimer();
}

$("#btn-timer").addEventListener("click", () => {
  $$('input[name="tmode"]').forEach((r) => (r.checked = r.value === timer.mode));
  $("#t-minutes").value = timer.minutes;
  $("#t-alerts").value = timer.alerts.join(", ");
  $("#timer").showModal();
});

$$('input[name="tmode"]').forEach((r) =>
  r.addEventListener("change", () => {
    timer.mode = r.value;
    saveTimer();
  })
);
$("#t-minutes").addEventListener("change", (e) => {
  timer.minutes = Math.max(1, +e.target.value || 15);
  syncFired();
  saveTimer();
});
$("#t-alerts").addEventListener("change", (e) => {
  timer.alerts = e.target.value
    .split(/[,; ]+/)
    .map(Number)
    .filter((n) => n > 0);
  syncFired();
  saveTimer();
});
$("#t-toggle").addEventListener("click", () => {
  if (timer.running) {
    timer.elapsedBefore = elapsed();
    timer.running = false;
  } else {
    timer.startedAt = Date.now();
    timer.running = true;
  }
  saveTimer();
});
$("#t-reset").addEventListener("click", () => {
  Object.assign(timer, { running: false, elapsedBefore: 0, startedAt: 0, fired: [] });
  saveTimer();
});

setInterval(renderTimer, 250);

// --- init ----------------------------------------------------------------------

setMode(settings.mode);
renderTimer();
connect();

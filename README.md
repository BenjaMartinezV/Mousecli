<div align="center">

<img src="src/mousecli/web/icon.svg" alt="Mousecli" width="128">

# Mousecli

**Convierte tu teléfono en un control de presentaciones.**

Pasa diapositivas, usa un puntero láser, controla el volumen, mueve el mouse y dicta texto en tu PC, sin instalar nada en el teléfono.

[![Release](https://img.shields.io/github/v/release/BenjaMartinezV/Mousecli?label=versi%C3%B3n)](https://github.com/BenjaMartinezV/Mousecli/releases/latest)
[![CI](https://github.com/BenjaMartinezV/Mousecli/actions/workflows/ci.yml/badge.svg)](https://github.com/BenjaMartinezV/Mousecli/actions/workflows/ci.yml)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-blue.svg)](LICENSE)
![Plataformas](https://img.shields.io/badge/plataformas-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

[**Descargar**](https://github.com/BenjaMartinezV/Mousecli/releases/latest) · [Reportar un error](https://github.com/BenjaMartinezV/Mousecli/issues/new/choose) · [Contribuir](CONTRIBUTING.md)

<img src="docs/screenshot.png" alt="Capturas de la app en el teléfono: puntero láser, modo mouse y timer" width="840">

</div>

---

## Tabla de contenidos

- [Características](#características)
- [Inicio rápido](#inicio-rápido)
- [Cómo funciona](#cómo-funciona)
- [Uso](#uso)
- [Apple Watch](#apple-watch)
- [Compatibilidad](#compatibilidad)
- [Solución de problemas](#solución-de-problemas)
- [Seguridad](#seguridad)
- [Desarrollo](#desarrollo)
- [Hoja de ruta](#hoja-de-ruta)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

## Características

| Función | Descripción |
|---|---|
| **Diapositivas** | Botones grandes para avanzar y retroceder. Funciona con PowerPoint, Google Slides, Keynote, Canva, visores de PDF y cualquier aplicación que use las flechas del teclado. |
| **Puntero láser** | Un punto rojo con estela que se dibuja sobre la presentación y se controla deslizando el dedo. No mueve el mouse real ni interfiere con la presentación. |
| **Pantalla completa** | Un botón inicia la presentación en pantalla completa desde la diapositiva actual y, al tocarlo de nuevo, sale de ella. |
| **Volumen** | Subir, bajar y silenciar. Mantener presionado repite la acción. |
| **Modo mouse** | El teléfono funciona como touchpad: deslizar mueve el cursor, tocar hace clic, tocar con dos dedos hace clic derecho y deslizar con dos dedos hace scroll. |
| **Texto y dictado** | Escribe o dicta con el micrófono del teclado del teléfono y el texto se escribe en el PC. Incluye atajos para Enter, Tab, Esc, borrar y F5. |
| **Timer configurable** | Cuenta regresiva o cronómetro, con alertas en los minutos que elijas. Vibra y cambia de color (verde, amarillo, rojo) a medida que se acaba el tiempo. |
| **Multi-pantalla** | El láser se muestra por defecto en la pantalla secundaria (proyector), con opción de cambiarla desde el teléfono. |
| **Apple Watch** | Pasa diapositivas con un gesto de la mano desde el Apple Watch, sin instalar nada en el reloj. Ver [Apple Watch](#apple-watch). |

## Inicio rápido

1. Descarga el archivo para tu sistema desde la [última versión](https://github.com/BenjaMartinezV/Mousecli/releases/latest):

   | Sistema | Archivo |
   |---|---|
   | Windows 10 y 11 | `Mousecli-vX.Y.Z-windows.zip` |
   | macOS 12 o superior | `Mousecli-vX.Y.Z-macos.zip` |
   | Linux | `Mousecli-vX.Y.Z-linux.zip` |

2. Descomprime el archivo y abre **Mousecli**. Aparecerá una ventana con un código QR.
3. Conecta el teléfono a la misma red WiFi que el PC y escanea el QR con la cámara.

No es necesario instalar Python ni usar la terminal.

> **Primera ejecución.** Como la aplicación no está firmada digitalmente, el sistema puede mostrar una advertencia:
>
> - **Windows:** si aparece "Windows protegió su PC", haz clic en *Más información* y luego en *Ejecutar de todas formas*. Si el firewall pregunta, permite el acceso en **redes privadas**.
> - **macOS:** haz clic derecho sobre la aplicación, elige *Abrir* y confirma. Luego autoriza Mousecli en *Ajustes del Sistema > Privacidad y seguridad > Accesibilidad*.
> - **Linux:** si el archivo no se abre, dale permisos de ejecución con `chmod +x Mousecli`.

<details>
<summary><b>Instalación con Python (para usuarios avanzados)</b></summary>

Requiere Python 3.9 o superior.

```bash
pipx install git+https://github.com/BenjaMartinezV/Mousecli.git
mousecli
```

</details>

## Cómo funciona

```
 Teléfono (navegador)                      PC
 ┌───────────────────┐   WebSocket    ┌─────────────────────────────┐
 │   Web app         │ ─────────────> │  Mousecli                   │
 │   (sin instalar)  │   WiFi local   │   - simula teclado y mouse  │
 └───────────────────┘                │   - dibuja el puntero láser │
                                      └─────────────────────────────┘
```

Mousecli ejecuta un pequeño servidor en el PC que también entrega la web app del teléfono. Al escanear el QR, el teléfono abre una conexión WebSocket persistente sobre la red local, con una latencia típica de 5 a 20 ms. El movimiento del dedo se agrupa y se envía como máximo una vez por cuadro de pantalla, lo que mantiene el láser fluido sin saturar la red.

No se usa internet ni servicios externos: todo ocurre entre el teléfono y el PC.

## Uso

### En una presentación

1. Conecta el proyector y abre la presentación en el PC. Haz clic una vez sobre ella para que tenga el foco del teclado.
2. Usa el teléfono:
   - El botón de pantalla completa inicia la presentación desde la diapositiva actual. Tócalo de nuevo para salir.
   - Los botones grandes pasan las diapositivas.
   - Mantén el dedo sobre el panel central para mostrar el láser y muévelo.
   - Los otros botones pequeños controlan el volumen.
   - El reloj de la esquina superior abre el timer.

El botón de pantalla completa usa el atajo de PowerPoint y LibreOffice Impress (`Shift+F5`, o `Cmd+Enter` en macOS). En otras aplicaciones, como Google Slides o Keynote, inicia la presentación desde el PC y usa el teléfono para todo lo demás.

Para que el teléfono abra Mousecli como una aplicación, usa *Agregar a pantalla de inicio* en el menú del navegador.

### Ajustes

Desde el engranaje de la web app puedes ajustar la sensibilidad del láser y del mouse, el tamaño del láser, la vibración de los botones y la pantalla donde aparece el láser.

### Opciones de línea de comandos

| Opción | Descripción |
|---|---|
| `--port N` | Puerto del servidor (por defecto `8765`). |
| `--host IP` | IP que se muestra en el QR, útil si el PC tiene varias redes. |
| `--no-gui` | Ejecuta sin ventana ni puntero láser, solo en la terminal. |
| `--new-token` | Genera un token nuevo. Los teléfonos guardados tendrán que escanear el QR otra vez. |
| `-v`, `--verbose` | Muestra información de depuración. |

## Apple Watch

Puedes pasar diapositivas desde el Apple Watch con un gesto de la mano, sin instalar nada en el reloj. Se usan dos funciones que ya trae el sistema: la app **Atajos** del iPhone y **AssistiveTouch** del reloj. El iPhone y el reloj deben estar en la misma red que el PC.

### 1. Crear los atajos en el iPhone

1. Abre Mousecli en el iPhone escaneando el QR, ve a *Ajustes* y despliega **Apple Watch y Atajos**.
2. Toca *Copiar* junto a "Siguiente diapositiva".
3. Abre la app **Atajos**, crea un atajo nuevo y agrega la acción **Obtener contenido de URL**. Pega la dirección copiada.
4. Nombra el atajo "Siguiente diapositiva".
5. Mantén presionado el atajo, toca **Detalles** y activa **Mostrar en Apple Watch**. Sin este paso, el atajo no aparece en el reloj.
6. Repite los pasos con "Diapositiva anterior".

Toca el atajo una vez en el iPhone para probarlo: la diapositiva debería avanzar. La primera vez, iOS puede pedir permiso para acceder a la red local; acéptalo.

### 2. Asignar los atajos a gestos en el reloj

1. En el Apple Watch, abre **Configuración > Accesibilidad > AssistiveTouch** y actívalo.
2. Entra en **Gestos con la mano** y actívalo.
3. Toca el gesto **juntar los dedos** (*Pinch*), baja hasta la sección de **Atajos** y elige "Siguiente diapositiva".
4. Toca el gesto **juntar los dedos dos veces** (*Double Pinch*) y elige "Diapositiva anterior".

También puedes configurarlo desde el iPhone, en la app **Watch > Accesibilidad > AssistiveTouch > Gestos con la mano**.

### 3. Presentar

- Levanta la muñeca para encender la pantalla del reloj y junta los dedos para avanzar.
- Si el gesto no responde, revisa la opción **Gesto de activación** en el mismo menú. Si está encendida, primero hay que **cerrar el puño dos veces** para activar AssistiveTouch.
- Los mismos atajos también funcionan con Siri ("Siguiente diapositiva"), desde una complicación de la esfera o con el botón de acción del Apple Watch Ultra.

> **Nota:** el doble toque del sistema del Apple Watch (Series 9 o posterior) no se puede asignar a un atajo, por eso se usa AssistiveTouch. Al activar AssistiveTouch, ese doble toque queda desactivado.

Las direcciones incluyen tu token privado: no las compartas. Si generas un token nuevo con `--new-token`, tendrás que copiarlas y actualizar los atajos.

## Compatibilidad

| Función | Windows | macOS | Linux (X11) | Linux (Wayland) |
|---|---|---|---|---|
| Diapositivas, texto y mouse | Sí | Sí | Sí | Limitado |
| Volumen | Sí | Sí | Sí | Sí |
| Puntero láser | Sí | Sí | Sí | Limitado |

En el teléfono funciona con cualquier navegador moderno: Chrome, Safari, Firefox, Edge o Samsung Internet.

**macOS:** Mousecli no muestra ícono en el Dock, para no quitarle el foco a la presentación. Ciérralo con el botón *Salir* de su ventana.

**Linux con Wayland:** por diseño de seguridad, Wayland restringe la simulación de teclado y las ventanas superpuestas. Se recomienda iniciar sesión en X11.

**WSL:** Mousecli debe ejecutarse en Windows, no dentro de WSL, ya que desde WSL no es posible controlar el teclado ni el mouse de Windows.

## Solución de problemas

**El teléfono no se conecta.**
- Verifica que el teléfono y el PC estén en la misma red WiFi.
- En Windows, la red debe estar configurada como **privada** (*Configuración > Red e Internet > Propiedades*).
- Muchas redes de universidades, empresas y hoteles bloquean la comunicación entre dispositivos. En ese caso, activa el hotspot del teléfono y conecta el PC a él. Es la opción más confiable.
- Si el PC tiene varias interfaces de red (VPN, máquinas virtuales), indica la IP correcta con `--host`.

**Los botones no hacen nada en la presentación.**
La ventana de la presentación debe tener el foco. Haz clic sobre ella una vez.

**Aparece "No se pudo abrir el puerto".**
Mousecli ya está abierto. Búscalo en la barra de tareas.

**La pantalla del teléfono se apaga.**
Los navegadores solo permiten mantener la pantalla encendida en conexiones HTTPS. Aumenta el tiempo de apagado de pantalla del teléfono durante la presentación. Mousecli se reconecta automáticamente al volver.

**El láser aparece en la pantalla equivocada.**
Abre *Ajustes* en el teléfono y presiona *Cambiar* en "Pantalla del láser".

**Registro de errores.**
La aplicación guarda un registro en `mousecli.log`, ubicado en `%APPDATA%\Mousecli` (Windows), `~/Library/Application Support/Mousecli` (macOS) o `~/.config/mousecli` (Linux). Adjúntalo al [reportar un error](https://github.com/BenjaMartinezV/Mousecli/issues/new/choose).

## Seguridad

- El servidor solo es accesible desde la red local y no usa servicios externos.
- Cada instalación genera un token privado que va incluido en el QR. Solo los dispositivos que lo escanean pueden conectarse.
- Si se desconecta el teléfono, el láser se oculta automáticamente.

Consulta [SECURITY.md](SECURITY.md) para más detalles y para reportar vulnerabilidades.

## Desarrollo

```bash
git clone https://github.com/BenjaMartinezV/Mousecli.git
cd Mousecli
pip install -e ".[dev]"
mousecli -v
```

Consulta [CONTRIBUTING.md](CONTRIBUTING.md) para la guía completa.

### Estructura del proyecto

```
src/mousecli/
├── cli.py          Punto de entrada: argumentos, token, QR y arranque
├── server.py       Servidor HTTP + WebSocket (aiohttp)
├── actions.py      Teclado, mouse y volumen (pynput)
├── gui.py          Capa transparente del láser y ventana del QR (PyQt6)
└── web/            Web app del teléfono (HTML, CSS y JavaScript sin dependencias)
scripts/
├── build.py        Compila la aplicación y genera el .zip para el sistema actual
└── make_icons.py   Genera los íconos PNG e ICO a partir de icon.svg
tests/              Tests del servidor y la configuración (pytest)
```

### Protocolo

El teléfono envía mensajes JSON cortos por WebSocket (`/ws?token=...`).

| Mensaje | Acción |
|---|---|
| `{"t":"key","k":"next"}` | Tecla con nombre: `next`, `prev`, `present` (pantalla completa), `end`, `start`, `enter`, `backspace`, `tab`, `esc`, `space` |
| `{"t":"vol","a":"up"}` | Volumen: `up`, `down`, `mute` |
| `{"t":"laser","on":true}` | Mostrar u ocultar el láser |
| `{"t":"lm","x":3.5,"y":-1}` | Mover el láser (relativo, en píxeles) |
| `{"t":"mm","x":4,"y":2}` | Mover el mouse (relativo, en píxeles) |
| `{"t":"click","b":"left"}` | Clic: `left` o `right` |
| `{"t":"scroll","y":-1}` | Scroll vertical, en pasos |
| `{"t":"type","s":"hola"}` | Escribir texto |
| `{"t":"cfg","size":14}` | Tamaño del láser |
| `{"t":"cfg","screen":"next"}` | Cambiar la pantalla del láser |
| `{"t":"ping","id":123}` | Medición de latencia |

El servidor responde con `hello` al conectar (versión y capacidades disponibles), `pong` y `screen` (nombre de la pantalla seleccionada).

Para clientes que no pueden mantener un WebSocket abierto, como Atajos de Apple, existe una API HTTP: `GET` o `POST` a `/api/<comando>?token=...`, que responde `{"ok": true, "command": "<comando>"}`. Los comandos disponibles son `next`, `prev`, `present`, `end`, `volume-up`, `volume-down` y `mute`. Las peticiones `HEAD` no ejecutan comandos, para que las vistas previas de enlaces no cambien de diapositiva.

### Compilar la aplicación

```bash
pip install . pyinstaller pillow
python scripts/build.py
```

El resultado queda en `dist/`. Al publicar un tag `v*`, GitHub Actions compila las versiones para Windows, macOS y Linux y las adjunta automáticamente al release.

## Hoja de ruta

- [x] Pasar diapositivas y conexión por QR
- [x] Puntero láser, pantalla completa, volumen y timer configurable
- [x] Modo mouse y dictado de texto
- [x] Aplicaciones descargables para Windows, macOS y Linux
- [x] Control desde Apple Watch y Siri mediante Atajos
- [ ] App nativa para Apple Watch con gestos de muñeca
- [ ] Lápiz y resaltador sobre la presentación
- [ ] Notas del orador y miniatura de la siguiente diapositiva
- [ ] Ícono en la bandeja del sistema
- [ ] Publicación en PyPI

## Contribuir

Las contribuciones son bienvenidas. Lee la [guía de contribución](CONTRIBUTING.md) antes de abrir un Pull Request. Para reportar errores o proponer mejoras, usa las [plantillas de issues](https://github.com/BenjaMartinezV/Mousecli/issues/new/choose).

## Licencia

Distribuido bajo la licencia MIT. Consulta [LICENSE](LICENSE) para más información.

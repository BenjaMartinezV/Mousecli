# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto sigue [Versionado Semántico](https://semver.org/lang/es/).

## [Sin publicar]

### Agregado

- Control desde Apple Watch, Siri y gestos de la mano mediante la app Atajos de Apple.
- API HTTP (`/api/<comando>?token=...`) para clientes que no usan WebSocket.
- Sección "Apple Watch y Atajos" en los ajustes de la web app, con las direcciones listas para copiar.

## [0.1.1] - 2026-10-08

### Corregido

- El clic con un toque en el modo mouse podía dejar de funcionar hasta recargar la página, si el teléfono perdía el aviso de que se levantó un dedo (por ejemplo, al bloquear la pantalla durante un toque).
- Los toques son más tolerantes a pequeños movimientos del dedo.
- En macOS, activar el láser ya no saca a PowerPoint de la presentación en pantalla completa.

## [0.1.0] - 2026-10-07

### Agregado

- Control de diapositivas desde el teléfono mediante una web app, sin instalación.
- Conexión por código QR con token privado persistente.
- Puntero láser con estela, dibujado en una capa transparente sobre la presentación.
- Botón para entrar y salir de la presentación en pantalla completa.
- Control de volumen con repetición al mantener presionado.
- Modo mouse: mover, clic, clic derecho y scroll con dos dedos.
- Modo texto con soporte para dictado mediante el teclado del teléfono.
- Timer configurable con cuenta regresiva o cronómetro, alertas y vibración.
- Selección de la pantalla del láser en configuraciones con proyector.
- Aplicaciones descargables para Windows, macOS y Linux.

[Sin publicar]: https://github.com/BenjaMartinezV/Mousecli/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/BenjaMartinezV/Mousecli/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/BenjaMartinezV/Mousecli/releases/tag/v0.1.0

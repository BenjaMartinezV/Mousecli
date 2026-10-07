# Política de seguridad

Mousecli permite controlar el teclado y el mouse de un PC, por lo que la seguridad es una prioridad.

## Modelo de seguridad

- El servidor solo es accesible desde la red local. No se expone a internet ni usa servicios externos.
- Cada instalación genera un token aleatorio que se incluye en el código QR. Las conexiones sin un token válido se rechazan.
- El token se guarda en la carpeta de configuración del usuario. Puedes regenerarlo con `mousecli --new-token` si crees que fue compartido.
- La conexión no está cifrada (HTTP en la red local). Evita usar Mousecli en redes públicas que no sean de confianza; en ese caso, usa el hotspot de tu teléfono.

## Reportar una vulnerabilidad

No abras un issue público para reportar vulnerabilidades. Usa la opción
[Report a vulnerability](https://github.com/BenjaMartinezV/Mousecli/security/advisories/new)
de la pestaña Security del repositorio. Responderemos lo antes posible.

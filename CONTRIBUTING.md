# Guía de contribución

Gracias por tu interés en mejorar Mousecli. Esta guía explica cómo preparar el entorno y qué se espera de una contribución.

## Entorno de desarrollo

Requisitos: Python 3.9 o superior y Git.

```bash
git clone https://github.com/BenjaMartinezV/Mousecli.git
cd Mousecli
python -m venv .venv
```

Activa el entorno virtual (`.venv\Scripts\activate` en Windows, `source .venv/bin/activate` en macOS y Linux) e instala el proyecto en modo editable con las herramientas de desarrollo:

```bash
pip install -e ".[dev]"
```

Ejecuta Mousecli desde el código fuente con:

```bash
mousecli -v
```

La web app del teléfono está en `src/mousecli/web/` y no requiere compilación: basta con recargar la página en el teléfono para ver los cambios.

## Antes de abrir un Pull Request

```bash
ruff check .
ruff format .
pytest
```

- Mantén los cambios enfocados: un PR por funcionalidad o corrección.
- Si cambias la interfaz del teléfono, pruébala en un dispositivo real. El comportamiento táctil no se puede verificar bien desde un navegador de escritorio.
- Si agregas un mensaje al protocolo, documéntalo en la sección "Protocolo" del README y agrega un test en `tests/test_server.py`.
- Actualiza `CHANGELOG.md` en la sección "Sin publicar".

## Íconos

Los íconos PNG e ICO se generan a partir de `src/mousecli/web/icon.svg`:

```bash
python scripts/make_icons.py
```

## Publicar una versión

1. Actualiza la versión en `pyproject.toml` y `src/mousecli/__init__.py`.
2. Mueve los cambios de "Sin publicar" a la nueva versión en `CHANGELOG.md`.
3. Crea y sube el tag:

```bash
git tag v0.2.0
git push origin v0.2.0
```

GitHub Actions compilará las aplicaciones para Windows, macOS y Linux y las publicará en la página de Releases.

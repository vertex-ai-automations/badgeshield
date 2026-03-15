# Installation

## Requirements

- Python **3.8 or later**
- Jinja2 (auto-installed)
- pylogshield (auto-installed)
- Typer + Rich (auto-installed)

## Install from PyPI

```bash
pip install badgeshield
```

Upgrade to the latest release:

```bash
pip install --upgrade badgeshield
```

## Optional: Image support

Logo embedding and color tinting require [Pillow](https://pillow.readthedocs.io/). Install it with the `image` extra:

```bash
pip install "badgeshield[image]"
```

Without Pillow, badges are still generated correctly — logos are embedded as-is (no tinting) and text widths fall back to a character-width estimator.

## Development install

Clone the repository and install in editable mode:

```bash
git clone https://github.com/vertex-ai-automations/badgeshield.git
cd badgeshield
pip install -e ".[image]"
pip install -r requirements.txt
```

## Verify the installation

```bash
python -c "import badgeshield; print(badgeshield.__version__)"
badgeshield --help
```

You should see the version number and the CLI help text.

!!! tip "Virtual environments"
    Always install into a virtual environment (`python -m venv .venv`) to avoid dependency conflicts.

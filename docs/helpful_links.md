# Helpful Links

## BadgeShield

- [PyPI package](https://pypi.org/project/badgeshield/)
- [GitHub repository](https://github.com/vertex-ai-automations/badgeshield)
- [Issue tracker](https://github.com/vertex-ai-automations/badgeshield/issues)
- [Changelog](https://github.com/vertex-ai-automations/badgeshield/releases)

## Dependencies

- [Typer](https://typer.tiangolo.com/) — CLI framework powering `badgeshield`'s subcommands
- [Rich](https://rich.readthedocs.io/) — terminal output, progress bars, and error panels
- [Jinja2](https://jinja.palletsprojects.com/) — SVG template rendering
- [Pillow](https://pillow.readthedocs.io/) — optional; enables accurate font metrics and logo tinting
- [pylogshield](https://pypi.org/project/pylogshield/) — structured logging used internally

## SVG & Badge Ecosystem

- [SVG specification (W3C)](https://www.w3.org/TR/SVG2/) — reference for understanding generated SVG output
- [shields.io](https://shields.io/) — popular hosted badge service (requires network; badgeshield is the offline alternative)
- [Simple Icons](https://simpleicons.org/) — brand icon SVGs suitable for use as badgeshield logos

## Python Tooling

- [coverage.py](https://coverage.readthedocs.io/) — generates `coverage.xml` consumed by `badgeshield coverage`
- [pytest](https://docs.pytest.org/) — test runner; JUnit XML output supported by `badgeshield preset tests`
- [setuptools-scm](https://setuptools-scm.readthedocs.io/) — version tagging from git used by badgeshield internally

## MkDocs

- [MkDocs](https://www.mkdocs.org/) — static site generator used for this documentation
- [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) — theme powering the docs site
- [mkdocstrings](https://mkdocstrings.github.io/) — auto-generates API reference from docstrings

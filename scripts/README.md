# scripts

Python scripts that build the slide catalog and the presentation.

- `build_deck.py`: builds `build/defensa.pptx` and `build/guion.md` from `content/01-defensa.yml`. Run `python scripts/build_deck.py --models` to list the patterns and their fields.
- `make_catalog.py`: maintainers only. Rebuilds `templates/utem-defense-template.potx` from the source defense deck.
- `pptx_tools.py`: helpers shared by both scripts.

Install the dependencies once with `pip install -r requirements.txt`.

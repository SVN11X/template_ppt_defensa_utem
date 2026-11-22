# template_ppt_defensa_utem

A template to build a UTEM thesis defense presentation with Claude Code, from a catalog of slides based on a real defense.

**Guía en español: [content/00-guia.md](content/00-guia.md).**

## For whom

UTEM undergraduate students of any program who are preparing their thesis defense ("defensa de título") and want slides in the institutional style, a speaker script with times and a rehearsal plan.

## Use it

1. Press **Use this template** on GitHub to create your own repository. Keep it private while your thesis is not public.
2. Install Python 3.11, then run once:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `thesis` folder and put the PDF of your thesis in it. Git ignores that folder.
4. Open Claude Code in the repository and run `/build-defense`. It writes `content/01-defensa.yml` and `content/02-ensayos.md`.
5. Review the text, complete every [bracket] and add your images to `figures/`.
6. Build the presentation:
   ```bash
   python scripts/build_deck.py
   ```
   It writes `build/defensa.pptx`, with the speaker script in the notes, and `build/guion.md`.

Run `python scripts/build_deck.py --models` to list the 17 slide patterns and their fields. Without Claude Code, edit `content/01-defensa.yml` by hand, or open `templates/utem-defense-template.potx` in PowerPoint and copy the patterns you need.

## How it works

`docs/how-it-works.md` explains the main flow from start to finish, each part with its path, where to start reading the code and how to check that it works.

## Status

Usable draft. The catalog, the build, the guide and the Claude Code skill work. CI builds the example content on every pull request.

## Layout

- `content/`: the guide, the slide content and the rehearsal plan, in Spanish.
- `templates/`: the slide catalog, the UTEM logos and the UTEM visual identity manual.
- `figures/`: the images your slides use.
- `scripts/`: the build script and the catalog script.
- `tests/`: tests of the build script.
- `bibliography/`: references, if your slides cite any.
- `docs/`: goals, how it works, references, glossary, decisions.

## Contributing

Tasks use the Task issue form. Pull requests follow `.github/pull_request_template.md`. Rules for people and AI tools are in `AGENTS.md`.

## Standard

This repository follows `SVN11X/standards@v1` with the `docs` profile. `AGENTS.md` is generated, so do not edit it by hand. To regenerate it or run the check locally:

```bash
pip install pyyaml
git clone --depth 1 --branch v1 https://github.com/SVN11X/standards .standards
python .standards/scripts/standard.py agents .
python .standards/scripts/standard.py check .
```

## License

CC-BY-4.0. See LICENSE. The UTEM logos and the visual identity manual in `templates/` belong to Universidad Tecnológica Metropolitana and are not covered by this license.

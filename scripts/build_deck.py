"""Build the defense presentation from content/01-defensa.yml and the slide catalog.

Each entry under "laminas" names a pattern ("modelo") of
templates/utem-defense-template.potx. The script copies that pattern, fills
its {{markers}} with the entry's fields, writes the speaker script into the
notes and saves build/defensa.pptx and build/guion.md.

Usage:
    python scripts/build_deck.py            build the presentation
    python scripts/build_deck.py --models   list every pattern and its fields
    python scripts/build_deck.py --strict   fail when a required field is missing
"""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

import yaml
from PIL import Image
from pptx.chart.data import CategoryChartData
from pptx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pptx_tools import (  # noqa: E402
    MARKER, clone_slide, delete_slide, drop_unused_relationships, iter_shapes, open_presentation,
    remove_sections, save_presentation, set_notes,
)

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "utem-defense-template.potx"
CONTENT = ROOT / "content" / "01-defensa.yml"
OUTPUT = ROOT / "build" / "defensa.pptx"
ACTIVE_BAR = "78BF26"
OPTIONAL_FIELDS = {"bajada", "fuente", "nota", "detalle", "etiqueta", "imagen"}
DEFAULTS = {"agenda": {"pie": "Estructura"}}
MODEL_LABELS = {"portada": "Portada", "agenda": "Estructura de la defensa", "cierre": "Cierre"}


class BuildError(Exception):
    pass


def flatten(value, prefix: str = "") -> dict[str, str]:
    """Turn nested fields into marker keys: cifras: [{valor: 3}] gives cifras.1.valor."""
    result: dict[str, str] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            result.update(flatten(item, f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(value, list):
        for index, item in enumerate(value, 1):
            result.update(flatten(item, f"{prefix}.{index}"))
    elif value is not None and not isinstance(value, bool):
        text = str(value).strip()
        if text:
            result[prefix] = text
    return result


class Fields:
    def __init__(self, values: dict[str, str]):
        self.values = values

    def present(self, key: str) -> bool:
        return key in self.values or any(k.startswith(key + ".") for k in self.values)

    def missing_item(self, key: str) -> bool:
        """True when the key belongs to a list item that the slide does not have."""
        parts = key.split(".")
        for end in range(2, len(parts) + 1):
            if parts[end - 1].isdigit() and not self.present(".".join(parts[:end])):
                return True
        return False


def load_content(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for section in ("defensa", "secciones", "laminas"):
        if section not in data:
            raise BuildError(f"{path.name}: missing the '{section}' section.")
    if len(data["secciones"]) != 5:
        raise BuildError(f"{path.name}: 'secciones' must list exactly 5 sections, like the tabs of the template.")
    return data


def patterns_of(prs) -> dict:
    return {slide.name: slide for slide in prs.slides if slide.name}


def slide_values(data: dict, slide: dict, position: int, page: str, hidden: bool) -> Fields:
    sections = data["secciones"]
    values = flatten(data["defensa"])
    values.update(flatten(DEFAULTS.get(slide["modelo"], {})))
    values.update(flatten({k: v for k, v in slide.items() if k not in ("modelo", "guion", "segundos", "oculta")}))
    for number, section in enumerate(sections, 1):
        values[f"pestana.{number}"] = str(section.get("pestana", ""))
        values[f"secciones.{number}.numero"] = f"{number:02d}"
        values[f"secciones.{number}.nombre"] = str(section.get("nombre", ""))
        values[f"secciones.{number}.detalle"] = str(section.get("detalle", ""))
    current = slide.get("seccion")
    if current:
        if not 1 <= int(current) <= len(sections):
            raise BuildError(f"Slide {position}: 'seccion' must be a number from 1 to {len(sections)}.")
        section = sections[int(current) - 1]
        values["seccion.numero"] = f"{int(current):02d}"
        values["seccion.nombre"] = str(section.get("nombre", ""))
        values["seccion.detalle"] = str(section.get("detalle", ""))
    if hidden:
        values["pie.seccion"] = "Respaldo"
    elif current:
        values["pie.seccion"] = values["seccion.nombre"]
    else:
        values["pie.seccion"] = values.get("pie", "")
    values["pie.pagina"] = page
    return Fields({k: v for k, v in values.items() if v})


def style_tabs(slide, section: int | None) -> None:
    """Highlight the tab of the current section with the pattern's own active style."""
    tabs = {s.name.split(":")[1]: s for s in slide.shapes if s.name.startswith("tab:")}
    bars = {s.name.split(":")[1]: s for s in slide.shapes if s.name.startswith("tabbar:")}

    def bar_color(shape):
        fill = shape._element.spPr.find(qn("a:solidFill"))
        color = fill.find(qn("a:srgbClr")) if fill is not None else None
        return color.get("val") if color is not None else None

    active = next((k for k, bar in bars.items() if bar_color(bar) == ACTIVE_BAR), None)
    inactive = next((k for k in bars if k != active), None)
    if not section or active is None or inactive is None:
        return
    styles = {}
    for kind, key in (("on", active), ("off", inactive)):
        run = tabs[key].text_frame.paragraphs[0].runs[0]._r
        styles[kind] = (copy.deepcopy(run.find(qn("a:rPr"))),
                        copy.deepcopy(bars[key]._element.spPr.find(qn("a:solidFill"))))
    for key, tab in tabs.items():
        run_style, fill = styles["on" if key == str(section) else "off"]
        for paragraph in tab.text_frame.paragraphs:
            for run in paragraph.runs:
                old = run._r.find(qn("a:rPr"))
                if old is not None:
                    run._r.remove(old)
                run._r.insert(0, copy.deepcopy(run_style))
        if key in bars:
            sp_pr = bars[key]._element.spPr
            old_fill = sp_pr.find(qn("a:solidFill"))
            old_fill.addprevious(copy.deepcopy(fill))
            sp_pr.remove(old_fill)


def keys_in(element) -> list[str]:
    return [key for node in element.iter(qn("a:t")) for key in MARKER.findall(node.text or "")]


def remove(element) -> None:
    if element.getparent() is not None:
        element.getparent().remove(element)


def replace_picture(slide, shape, path: Path) -> None:
    with Image.open(path) as image:
        width, height = image.size
    scale = min(shape.width / width, shape.height / height)
    new_width, new_height = int(width * scale), int(height * scale)
    left = shape.left + (shape.width - new_width) // 2
    top = shape.top + (shape.height - new_height) // 2
    picture = slide.shapes.add_picture(str(path), left, top, new_width, new_height)
    shape._element.addprevious(picture._element)
    remove(shape._element)
    picture.name = shape.name


def fill_chart(shape, spec) -> None:
    data = CategoryChartData()
    data.categories = [str(c) for c in spec["categorias"]]
    series = spec.get("series") or [{"nombre": spec.get("serie", ""), "valores": spec["valores"]}]
    for item in series:
        data.add_series(str(item.get("nombre", "")), [float(v) for v in item["valores"]])
    shape.chart.replace_data(data)


def fill_slide(slide, fields: Fields, raw: dict, content_dir: Path, position: int, warnings: list[str]) -> None:
    for shape in list(iter_shapes(slide.shapes)):
        name = shape.name
        if name.startswith("item:") and not fields.present(name[5:]):
            remove(shape._element)
        elif name.startswith("img:"):
            _, key, mode = name.split(":")
            value = fields.values.get(key)
            if value and value.startswith("["):
                value = None  # still a [placeholder]
            if fields.missing_item(key) or (not value and mode == "remove"):
                remove(shape._element)
            elif value:
                path = (content_dir.parent / value) if not Path(value).is_absolute() else Path(value)
                if not path.exists():
                    warnings.append(f"Slide {position}: image not found: {value}")
                else:
                    replace_picture(slide, shape, path)
            else:
                warnings.append(f"Slide {position}: add the image '{key}' (the placeholder stays).")
        elif name.startswith("chart:"):
            key = name[6:]
            if isinstance(raw.get(key), dict) and "categorias" in raw[key]:
                fill_chart(shape, raw[key])
            else:
                warnings.append(f"Slide {position}: add '{key}' with 'categorias' and 'valores' (example data stays).")

    tree = slide.shapes._spTree
    for row in list(tree.iter(qn("a:tr"))):
        keys = keys_in(row)
        if keys and all(fields.missing_item(k) for k in keys):
            remove(row)
    for paragraph in list(tree.iter(qn("a:p"))):
        keys = keys_in(paragraph)
        if keys and any(fields.missing_item(k) for k in keys):
            body = paragraph.getparent()
            if len(body.findall(qn("a:p"))) > 1:
                remove(paragraph)
            else:
                for text in paragraph.iter(qn("a:t")):
                    text.text = ""

    def value_of(match) -> str:
        key = match.group(1)
        if key in fields.values:
            return fields.values[key]
        if key.split(".")[-1] in OPTIONAL_FIELDS or key in OPTIONAL_FIELDS:
            return ""
        warnings.append(f"Slide {position}: missing '{key}'.")
        return f"[completar: {key}]"

    for text in tree.iter(qn("a:t")):
        if text.text and "{{" in text.text:
            text.text = MARKER.sub(value_of, text.text)


def build(content: Path, template: Path, output: Path) -> tuple[list[str], dict]:
    data = load_content(content)
    prs = open_presentation(template)
    patterns = patterns_of(prs)
    originals = list(prs.slides)
    slides = data["laminas"]
    hidden_flags = [bool(s.get("oculta", str(s.get("modelo", "")).startswith("respaldo-"))) for s in slides]
    total = sum(1 for hidden in hidden_flags if not hidden)
    warnings: list[str] = []
    script = []
    visible_number = 0
    for position, (slide_data, hidden) in enumerate(zip(slides, hidden_flags), 1):
        model = slide_data.get("modelo")
        if model not in patterns:
            raise BuildError(f"Slide {position}: unknown modelo '{model}'. Run --models to list them.")
        if not hidden:
            visible_number += 1
        page = f"Respaldo {position}" if hidden else f"{visible_number:02d} / {total:02d}"
        fields = slide_values(data, slide_data, position, page, hidden)
        slide = clone_slide(prs, patterns[model])
        style_tabs(slide, slide_data.get("seccion"))
        fill_slide(slide, fields, slide_data, content.parent, position, warnings)
        drop_unused_relationships(slide)
        if hidden:
            slide._element.set("show", "0")
        seconds = int(slide_data.get("segundos") or 0)
        spoken = str(slide_data.get("guion") or "").strip()
        set_notes(slide, f"({seconds} s) {spoken}" if spoken else "")
        title = (slide_data.get("titulo") or fields.values.get("seccion.nombre")
                 or MODEL_LABELS.get(model, model))
        script.append((position, title, seconds, spoken, hidden))
    for slide in originals:
        delete_slide(prs, slide)
    remove_sections(prs)
    save_presentation(prs, output)
    stats = write_script(script, data["defensa"], output.with_name("guion.md"), warnings)
    return warnings, stats


def write_script(script, defense: dict, path: Path, warnings: list[str]) -> dict:
    visible = sum(s for _, _, s, _, hidden in script if not hidden)
    target = int(defense.get("duracion_minutos") or 0)
    lines = ["# Guion de la defensa", "",
             f"Tiempo de las láminas visibles: {visible // 60} min {visible % 60} s"
             + (f" (objetivo: {target} min)." if target else "."), ""]
    for position, title, seconds, spoken, hidden in script:
        label = "Respaldo, oculta" if hidden else f"{seconds} s"
        lines += [f"## Lámina {position} · {title} ({label})", "", spoken or "[completar el guion]", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    if target and visible > target * 60:
        warnings.append(f"The visible slides take {visible} s, more than the {target} min target.")
    return {"slides": len(script), "visible_seconds": visible, "target_minutes": target}


def list_models(template: Path) -> None:
    prs = open_presentation(template)
    for name, slide in patterns_of(prs).items():
        keys = []
        for shape in iter_shapes(slide.shapes):
            if shape.name.startswith(("img:", "chart:")):
                keys.append(shape.name.split(":")[1])
        keys += keys_in(slide.shapes._spTree)
        hidden = {"pie.seccion", "pie.pagina", "titulo_profesional", "estudiante", "profesor_guia",
                  "carrera", "lugar_y_anio"}
        shown = sorted({k for k in keys if not k.startswith(("pestana.", "secciones.", "seccion.")) and k not in hidden})
        print(f"{name}: {', '.join(shown) or '(no fields, it uses the sections)'}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--content", type=Path, default=CONTENT)
    parser.add_argument("--template", type=Path, default=TEMPLATE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--models", action="store_true", help="list every pattern and its fields")
    parser.add_argument("--strict", action="store_true", help="fail when a required field is missing")
    args = parser.parse_args()
    if args.models:
        list_models(args.template)
        return 0
    try:
        warnings, stats = build(args.content, args.template, args.output)
    except BuildError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    for warning in warnings:
        print(f"Warning: {warning}")
    print(f"Wrote {args.output} ({stats['slides']} slides) and {args.output.with_name('guion.md')}. "
          f"Visible slides: {stats['visible_seconds']} s.")
    return 1 if args.strict and warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())

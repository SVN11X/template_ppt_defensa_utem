"""Build templates/utem-defense-template.potx from a finished defense deck.

Maintainers only. The source is the repository owner's own finished defense
deck, which is not part of this repository. The script
keeps one slide per pattern, turns its text into {{markers}}, swaps its
pictures for placeholders and its icons for a neutral icon, and removes the
author's data. build_deck.py later copies these patterns and fills the markers.

Usage:
    python scripts/make_catalog.py SOURCE.pptx templates/utem-defense-template.potx
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pptx.chart.data import CategoryChartData
from pptx.oxml.ns import qn
from pptx.shapes.autoshape import Shape
from pptx.util import Inches

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pptx_tools import (  # noqa: E402
    delete_slide, drop_unused_relationships, inches, iter_shapes, move_slide, open_presentation, remove_sections,
    remove_unused_layouts, save_presentation, set_notes, set_paragraphs,
)

LOGO_SHA1 = "67a9b0b1"
BLUE, GREEN, GRAY, LIGHT, LINE = "#004EAA", "#78BF26", "#6B7280", "#F3F4F6", "#E5E7EB"


def numbered(prefix: str, ids: list[tuple[int, int, int]]) -> dict:
    """Map (number, value id, text id) triples to markers, for agenda rows."""
    text = {}
    for number, *shape_ids in ids:
        for shape_id, field in zip(shape_ids, ("numero", "nombre", "detalle")):
            text[shape_id] = [f"{{{{{prefix}.{number}.{field}}}}}"]
    return text


def pairs(prefix: str, ids: list[tuple[int, int]], fields=("nombre", "texto")) -> dict:
    text = {}
    for number, id_pair in enumerate(ids, 1):
        for shape_id, field in zip(id_pair, fields):
            text[shape_id] = [f"{{{{{prefix}.{number}.{field}}}}}"]
    return text


def columns(prefix: str, count: int, left: float, width: float, top: float, bottom: float) -> dict:
    return {f"{prefix}.{n}": (left + width * (n - 1), top, left + width * n, bottom) for n in range(1, count + 1)}


PATTERNS = [
    dict(name="portada", source=1,
         hint="Portada: título de la tesis, una bajada y tus datos. La imagen es opcional.",
         text={5: [None], 6: ["{{titulo}}"], 7: ["{{bajada}}"],
               9: ["{{estudiante}}", "Profesor guía: {{profesor_guia}}", "{{carrera}}, UTEM", "{{lugar_y_anio}}"],
               13: ["Defensa de Título de {{titulo_profesional}}"], 14: ["{{pie.pagina}}"]},
         images={17: ("imagen", "remove")}),
    dict(name="agenda", source=2,
         hint="Estructura de la defensa. Toma los nombres y detalles de las cinco secciones.",
         text={13: [None], **numbered("secciones", [(1, 23, 24, 25), (2, 27, 28, 29), (3, 31, 32, 33),
                                                   (4, 35, 36, 37), (5, 39, 40, 41)])}),
    dict(name="separador", source=3,
         hint="Separador de sección. Toma número, nombre y detalle de la sección indicada.",
         text={14: ["{{seccion.numero}}"], 15: ["{{seccion.nombre}}"], 16: ["{{seccion.detalle}}"]}),
    dict(name="problema", source=4,
         hint="Problema: la pregunta central, dos contrastes, dos cifras y hasta cuatro puntos.",
         text={23: ["{{pregunta}}"],
               210: ["{{contraste.1.etiqueta}}", "{{contraste.1.texto}}"],
               212: ["{{contraste.2.etiqueta}}", "{{contraste.2.texto}}"],
               28: ["{{cifras.1.valor}}"], 29: ["{{cifras.1.texto}}"],
               26: ["{{cifras.2.valor}}"], 27: ["{{cifras.2.texto}}"],
               31: [[f"{{{{puntos.{n}.nombre}}}}:", f" {{{{puntos.{n}.texto}}}}"] for n in range(1, 5)]},
         item_ids={203: "puntos.1", 204: "puntos.2", 205: "puntos.3", 206: "puntos.4"},
         split={31: dict(items="puntos", icons=[203, 204, 205, 206], top=4.08, step=0.55, height=0.5)}),
    dict(name="objetivos", source=6,
         hint="Objetivos copiados textual de la tesis: el general y hasta cuatro específicos.",
         text={23: ["{{objetivo_general}}"],
               **pairs("especificos", [(26, 27), (30, 31), (34, 35), (38, 39)])},
         items={"especificos.1": (0.6, 3.45, 6.6, 5.4), "especificos.2": (6.6, 3.45, 12.7, 5.4),
                "especificos.3": (0.6, 5.4, 6.6, 6.9), "especificos.4": (6.6, 5.4, 12.7, 6.9)}),
    dict(name="imagen", source=8,
         hint="Una imagen grande, por ejemplo un diagrama de tu solución, con su fuente.",
         remove_regions=[(0.5, 1.2, 12.65, 6.9)], keep_ids=[95, 14],
         add_image=("imagen", (0.85, 1.5, 11.7, 4.85))),
    dict(name="dos-imagenes", source=9,
         hint="Dos imágenes lado a lado, cada una con una línea que dice qué muestra.",
         text={24: ["{{imagenes.1.texto}}"], 27: ["{{imagenes.2.texto}}"]},
         images={31: ("imagenes.1.archivo", "keep"), 29: ("imagenes.2.archivo", "keep")}),
    dict(name="tabla", source=10,
         hint="Tabla de hasta siete filas y, si quieres, un recuadro destacado con tres pasos.",
         text={47: ["{{destacado.titulo}}"],
               **{shape_id: [[f"{n}  ", f"{{{{destacado.pasos.{n}}}}}"]]
                  for n, shape_id in ((1, 740), (2, 742), (3, 744))}},
         tables={49: "tabla"}, items={"destacado": (0.6, 5.7, 12.7, 6.85)}),
    dict(name="cifras", source=12,
         hint="Hasta cuatro cifras grandes con lo que significan, y una lectura que las une.",
         text={22: ["{{cifras.1.valor}}"], 23: ["{{cifras.1.texto}}", "{{cifras.1.detalle}}"],
               24: ["{{cifras.2.valor}}"], 25: ["{{cifras.2.texto}}", "{{cifras.2.detalle}}"],
               26: ["{{cifras.3.valor}}"], 27: ["{{cifras.3.texto}}", "{{cifras.3.detalle}}"],
               31: ["{{cifras.4.valor}}"], 32: ["{{cifras.4.texto}}", "{{cifras.4.detalle}}"],
               29: [None], 30: ["{{lectura}}"]},
         items=columns("cifras", 4, 0.75, 2.9, 1.8, 4.4)),
    dict(name="grafico", source=13,
         hint="Un gráfico de barras grande, con una nota bajo él y su lectura al lado.",
         text={36: [None], 37: ["{{lectura.1}}"], 26: ["{{lectura.2}}"], 39: ["{{grafico.nota}}"]},
         charts={38: "grafico"}, remove_ids=[95, *range(600, 665)], resize={22: (None, 4.06), 23: (None, 4.06)}),
    dict(name="validacion", source=16,
         hint="Tabla de validación de hasta cinco filas y dos notas al lado.",
         text={44: ["{{notas.1.titulo}}"], 45: ["{{notas.1.texto}}"],
               48: ["{{notas.2.titulo}}"], 49: ["{{notas.2.texto}}"]},
         tables={50: "tabla"}, remove_ids=list(range(52, 66)), move={45: (None, 2.55)}),
    dict(name="conclusiones", source=18,
         hint="Conclusión ligada al problema, aporte, limitaciones y una frase final para recordar.",
         text={25: ["{{conclusion}}"], 29: ["{{aporte}}"], 33: ["{{limitaciones}}"],
               720: ["{{estado.1}}"], 721: ["{{estado.2}}"], 722: ["{{estado.3}}"], 723: ["{{estado.4}}"],
               35: [None], 36: ["{{mensaje_final}}"]},
         item_ids={720: "estado.1", 721: "estado.2", 722: "estado.3", 723: "estado.4"}),
    dict(name="cierre", source=19,
         hint="Cierre: gracias y preguntas. La imagen es opcional.",
         text={4: [None], 5: [None], 6: [None], 9: ["{{estudiante}} · {{carrera}} · UTEM"],
               11: ["Defensa de Título de {{titulo_profesional}}"], 13: ["{{pie.pagina}}"]}),
    dict(name="respaldo-tarjetas", source=23,
         hint="Respaldo oculto: cuatro preguntas probables, cada una con su cifra y explicación.",
         text={187: ["{{bajada}}"], 189: ["{{nota}}"], 257: ["{{conclusion}}"],
               **{shape_id: [f"{{{{tarjetas.{n}.{field}}}}}"]
                  for n, ids in enumerate([(201, 203, 205, 259, 207), (215, 217, 219, 261, 221),
                                           (229, 231, 233, 263, 235), (245, 247, 249, 265, 251)], 1)
                  for shape_id, field in zip(ids, ("etiqueta", "pregunta", "valor", "lectura", "texto"))}},
         items={"tarjetas.1": (0.6, 2.15, 6.6, 4.2), "tarjetas.2": (6.6, 2.15, 12.7, 4.2),
                "tarjetas.3": (0.6, 4.2, 6.6, 6.25), "tarjetas.4": (6.6, 4.2, 12.7, 6.25)}),
    dict(name="respaldo-pasos", source=24,
         hint="Respaldo oculto: cuatro pasos, una tabla y un recuadro con tres razones.",
         text={**pairs("pasos", [(26, 27), (30, 31), (34, 35), (38, 39)]),
               41: ["{{destacado.titulo}}"], 42: ["{{destacado.texto}}"],
               901: ["{{destacado.puntos.1}}"], 903: ["{{destacado.puntos.2}}"], 905: ["{{destacado.puntos.3}}"]},
         tables={40: "tabla"},
         items=columns("pasos", 4, 0.75, 2.95, 1.9, 3.6),
         item_ids={900: "destacado.puntos.1", 901: "destacado.puntos.1", 902: "destacado.puntos.2",
                   903: "destacado.puntos.2", 904: "destacado.puntos.3", 905: "destacado.puntos.3"}),
    dict(name="respaldo-antes-despues", source=25,
         hint="Respaldo oculto: antes y después, cada lado con imagen, explicación y fuente.",
         text={23: ["{{antes.titulo}}"], 28: ["{{antes.texto}}"], 45: ["{{antes.fuente}}"],
               32: ["{{despues.titulo}}"], 37: ["{{despues.texto}}"], 46: ["{{despues.fuente}}"]},
         images={44: ("antes.imagen", "keep"), 42: ("despues.imagen", "keep")},
         remove_ids=list(range(1100, 1120))),
    dict(name="respaldo-alcance", source=28,
         hint="Respaldo oculto: qué evaluó la tesis y qué quedó fuera del alcance.",
         text={26: ["{{dentro.titulo}}"], 29: ["{{fuera.titulo}}"], 31: ["{{nota}}"],
               950: ["{{dentro.puntos.1}}"], 952: ["{{dentro.puntos.2}}"], 954: ["{{dentro.puntos.3}}"],
               951: ["{{fuera.puntos.1}}"], 953: ["{{fuera.puntos.2}}"], 955: ["{{fuera.puntos.3}}"]},
         item_ids={950: "dentro.puntos.1", 958: "dentro.puntos.1", 952: "dentro.puntos.2", 959: "dentro.puntos.2",
                   954: "dentro.puntos.3", 960: "dentro.puntos.3", 951: "fuera.puntos.1", 961: "fuera.puntos.1",
                   953: "fuera.puntos.2", 962: "fuera.puntos.2", 955: "fuera.puntos.3", 963: "fuera.puntos.3"}),
]

TAB_TOP, BAR_TOP, FOOTER_TOP = 0.3, 0.4, 6.9
TAGS = ("tab:", "tabbar:", "footer:", "item:", "img:", "chart:", "table:", "logo", "icon")


def font(size: int):
    for name in ("calibri.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def placeholder_image(folder: Path, width: float, height: float) -> Path:
    size = (max(int(width * 150), 60), max(int(height * 150), 60))
    image = Image.new("RGB", size, LIGHT)
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, size[0] - 1, size[1] - 1], outline=LINE, width=4)
    label = "Tu imagen aquí"
    typeface = font(max(size[1] // 10, 14))
    box = draw.textbbox((0, 0), label, font=typeface)
    draw.text(((size[0] - box[2]) / 2, (size[1] - box[3]) / 2), label, fill=GRAY, font=typeface)
    path = folder / f"placeholder-{size[0]}x{size[1]}.png"
    image.save(path)
    return path


def neutral_icon(folder: Path) -> Path:
    path = folder / "icon.png"
    image = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse([10, 10, 118, 118], outline=BLUE, width=12)
    draw.ellipse([46, 46, 82, 82], fill=GREEN)
    image.save(path)
    return path


def picture_sha1(shape) -> str:
    try:
        return hashlib.sha1(shape.image.blob).hexdigest()[:8]
    except ValueError:
        return ""


def replace_picture(slide, shape, image_path: Path, name: str) -> None:
    new = slide.shapes.add_picture(str(image_path), shape.left, shape.top, shape.width, shape.height)
    shape._element.addprevious(new._element)
    shape._element.getparent().remove(shape._element)
    new.name = name


def center(shape) -> tuple[float, float]:
    return inches(shape.left + shape.width // 2), inches(shape.top + shape.height // 2)


def inside(point, box) -> bool:
    return box[0] <= point[0] < box[2] and box[1] <= point[1] < box[3]


def tag_frame(slide, explicit: set[int]) -> None:
    """Name the tabs, their bars and the footer, and mark title, subtitle and source."""
    top_level = list(slide.shapes)
    tabs = sorted((s for s in top_level if s.has_text_frame and inches(s.top) < TAB_TOP
                   and s.text_frame.text.strip()), key=lambda s: s.left)
    bars = sorted((s for s in top_level if not s.has_text_frame or not s.text_frame.text.strip()
                   if TAB_TOP - 0.05 < inches(s.top) < BAR_TOP and inches(s.height) < 0.06), key=lambda s: s.left)
    for index, shape in enumerate(tabs, 1):
        shape.name = f"tab:{index}"
        set_paragraphs(shape.text_frame, [f"{{{{pestana.{index}}}}}"])
    for index, shape in enumerate(bars, 1):
        shape.name = f"tabbar:{index}"
    for shape in top_level:
        if shape.shape_id in explicit or not shape.has_text_frame or not shape.text_frame.text.strip():
            continue
        left, top, text = inches(shape.left), inches(shape.top), shape.text_frame.text.strip()
        if top > FOOTER_TOP and left < 1:
            shape.name = "footer:section"
            set_paragraphs(shape.text_frame, ["{{pie.seccion}}"])
        elif top > FOOTER_TOP and left > 7:
            shape.name = "footer:page"
            set_paragraphs(shape.text_frame, ["{{pie.pagina}}"])
        elif abs(left - 0.66) < 0.05 and abs(top - 0.58) < 0.05:
            set_paragraphs(shape.text_frame, ["{{titulo}}"])
        elif abs(left - 0.66) < 0.05 and abs(top - 1.37) < 0.05:
            set_paragraphs(shape.text_frame, ["{{bajada}}"])
        elif text.startswith("Fuente"):
            set_paragraphs(shape.text_frame, ["{{fuente}}"])


def tag_table(shape, key: str) -> None:
    table = shape.table
    for row_index, row in enumerate(table.rows):
        for column_index, cell in enumerate(row.cells, 1):
            marker = (f"{{{{{key}.columnas.{column_index}}}}}" if row_index == 0
                      else f"{{{{{key}.filas.{row_index}.{column_index}}}}}")
            set_paragraphs(cell.text_frame, [marker])
    shape.name = f"table:{key}"


def reset_chart(shape, key: str) -> None:
    data = CategoryChartData()
    data.categories = [f"[Grupo {n}]" for n in range(1, 6)]
    data.add_series("[Medida]", (30, 40, 35, 45, 40))
    shape.chart.replace_data(data)
    chart_xml = shape.chart._chartSpace
    for point in list(chart_xml.iter(qn("c:dPt"))):
        point.getparent().remove(point)
    for scaling in chart_xml.iter(qn("c:scaling")):
        for limit in scaling.findall(qn("c:min")) + scaling.findall(qn("c:max")):
            scaling.remove(limit)
    for unit in list(chart_xml.iter(qn("c:majorUnit"), qn("c:minorUnit"))):
        unit.getparent().remove(unit)
    for number_format in chart_xml.iter(qn("c:numFmt")):
        number_format.set("formatCode", "General")
        number_format.set("sourceLinked", "0")
    shape.name = f"chart:{key}"


def split_points(slide, by_id: dict, shape_id: int, rule: dict) -> None:
    """Give each paragraph its own text box next to its icon, so the icons stay aligned."""
    source = by_id[shape_id]
    for index, icon_id in enumerate(rule["icons"]):
        top = rule["top"] + index * rule["step"]
        element = copy.deepcopy(source._element)
        source._element.addprevious(element)
        box = Shape(element, source._parent)
        paragraphs = box.text_frame.paragraphs
        for number, paragraph in enumerate(paragraphs):
            if number != index:
                paragraph._p.getparent().remove(paragraph._p)
        box.top, box.height = Inches(top - 0.03), Inches(rule["height"])
        box.name = f"item:{rule['items']}.{index + 1}"
        by_id[icon_id].top = Inches(top)
    source._element.getparent().remove(source._element)


def build_pattern(slide, spec: dict, folder: Path, icon: Path) -> None:
    by_id = {shape.shape_id: shape for shape in iter_shapes(slide.shapes)}
    explicit = set(spec.get("text", {}))
    keep = set(spec.get("keep_ids", []))

    for shape_id in spec.get("remove_ids", []):
        if shape_id in by_id:
            element = by_id[shape_id]._element
            if element.getparent() is not None:
                element.getparent().remove(element)
    for region in spec.get("remove_regions", []):
        for shape in list(slide.shapes):
            if shape.shape_id not in keep and inside(center(shape), region):
                shape._element.getparent().remove(shape._element)

    for shape_id, (width, height) in spec.get("resize", {}).items():
        shape = by_id[shape_id]
        if width:
            shape.width = Inches(width)
        if height:
            shape.height = Inches(height)
    for shape_id, (left, top) in spec.get("move", {}).items():
        shape = by_id[shape_id]
        if left is not None:
            shape.left = Inches(left)
        if top is not None:
            shape.top = Inches(top)

    for shape_id, paragraphs in spec.get("text", {}).items():
        set_paragraphs(by_id[shape_id].text_frame, paragraphs)
    for shape_id, key in spec.get("tables", {}).items():
        tag_table(by_id[shape_id], key)
    for shape_id, key in spec.get("charts", {}).items():
        reset_chart(by_id[shape_id], key)
    tag_frame(slide, explicit)
    for shape_id, rule in spec.get("split", {}).items():
        split_points(slide, by_id, shape_id, rule)

    for shape in list(slide.shapes):
        for key, box in spec.get("items", {}).items():
            if inside(center(shape), box) and not shape.name.startswith(("table:", "chart:")):
                shape.name = f"item:{key}"
    for shape_id, key in spec.get("item_ids", {}).items():
        if shape_id in by_id:
            by_id[shape_id].name = f"item:{key}"

    images = spec.get("images", {})
    for shape in [s for s in iter_shapes(slide.shapes) if s.shape_type == 13]:
        sha1 = picture_sha1(shape)
        if sha1 == LOGO_SHA1:
            shape.name = "logo"
        elif not sha1 or inches(shape.width) < 0.6:
            name = shape.name if shape.name.startswith("item:") else "icon"
            replace_picture(slide, shape, icon, name)
        else:
            key, mode = images.get(shape.shape_id, ("imagen", "remove"))
            path = placeholder_image(folder, inches(shape.width), inches(shape.height))
            replace_picture(slide, shape, path, f"img:{key}:{mode}")

    if "add_image" in spec:
        key, (left, top, width, height) = spec["add_image"]
        path = placeholder_image(folder, width, height)
        picture = slide.shapes.add_picture(str(path), Inches(left), Inches(top), Inches(width), Inches(height))
        picture.name = f"img:{key}:keep"

    for shape in iter_shapes(slide.shapes):
        if not shape.name.startswith(TAGS):
            shape.name = f"Shape {shape.shape_id}"  # the source names describe the author's thesis
    slide._element.cSld.set("name", spec["name"])
    if "show" in slide._element.attrib:
        del slide._element.attrib["show"]
    set_notes(slide, f"Modelo «{spec['name']}». {spec['hint']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    prs = open_presentation(args.source)
    slides = list(prs.slides)
    keep = [slides[spec["source"] - 1] for spec in PATTERNS]
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        icon = neutral_icon(folder)
        for slide, spec in zip(keep, PATTERNS):
            build_pattern(slide, spec, folder, icon)
            drop_unused_relationships(slide)
        for slide in slides:
            if not any(slide is kept for kept in keep):
                delete_slide(prs, slide)
        for index, slide in enumerate(keep):
            move_slide(prs, slide, index)
        remove_unused_layouts(prs)
        remove_sections(prs)
        core = prs.core_properties
        core.author = core.last_modified_by = ""
        core.title = "Plantilla de defensa de título UTEM"
        core.comments = core.keywords = core.subject = ""
        save_presentation(prs, args.output)
    print(f"Wrote {args.output} with {len(PATTERNS)} patterns.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

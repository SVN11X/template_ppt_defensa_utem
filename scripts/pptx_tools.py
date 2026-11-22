"""Helpers shared by make_catalog.py and build_deck.py to open, copy and save PowerPoint files."""
from __future__ import annotations

import copy
import io
import re
import zipfile
from collections.abc import Iterator
from pathlib import Path

from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn
from pptx.parts.chart import ChartPart
from pptx.parts.embeddedpackage import EmbeddedXlsxPart
from pptx.util import Emu

PRESENTATION_MAIN = "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"
TEMPLATE_MAIN = "application/vnd.openxmlformats-officedocument.presentationml.template.main+xml"
R_NAMESPACE = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
MARKER = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")
EMU_PER_INCH = 914400


def inches(value: int) -> float:
    return Emu(value) / EMU_PER_INCH


def _swap_main_type(data: bytes, old: str, new: str) -> bytes:
    """Rewrite [Content_Types].xml so a .potx opens as a presentation, or the reverse."""
    source = zipfile.ZipFile(io.BytesIO(data))
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target:
        for item in source.infolist():
            blob = source.read(item.filename)
            if item.filename == "[Content_Types].xml":
                blob = blob.replace(old.encode(), new.encode())
            target.writestr(item, blob)
    return output.getvalue()


def open_presentation(path: Path):
    """Open a .pptx or .potx file. python-pptx only reads the presentation content type."""
    data = Path(path).read_bytes()
    data = _swap_main_type(data, TEMPLATE_MAIN, PRESENTATION_MAIN)
    return Presentation(io.BytesIO(data))


def save_presentation(prs, path: Path) -> None:
    """Save as .pptx, or as a template when the path ends in .potx."""
    path = Path(path)
    buffer = io.BytesIO()
    prs.save(buffer)
    data = buffer.getvalue()
    if path.suffix.lower() == ".potx":
        data = _swap_main_type(data, PRESENTATION_MAIN, TEMPLATE_MAIN)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def iter_shapes(shapes) -> Iterator:
    """Every shape, including the shapes inside groups."""
    for shape in shapes:
        yield shape
        if shape.shape_type == 6:  # group
            yield from iter_shapes(shape.shapes)


def _copy_chart(chart: ChartPart, package) -> ChartPart:
    partname = package.next_partname(ChartPart.partname_template)
    new_chart = ChartPart.load(partname, chart.content_type, package, chart.blob)
    for rel in list(chart.rels.values()):
        if rel.reltype == RT.PACKAGE:
            workbook = EmbeddedXlsxPart.new(rel.target_part.blob, package)
            new_rid = new_chart.relate_to(workbook, RT.PACKAGE)
            for external in new_chart._element.iter(qn("c:externalData")):
                external.set(qn("r:id"), new_rid)
    return new_chart


def _copy_relationship(source_part, target_part, rid: str) -> str:
    rel = source_part.rels[rid]
    if rel.is_external:
        return target_part.relate_to(rel.target_ref, rel.reltype, is_external=True)
    if rel.reltype == RT.CHART:
        return target_part.relate_to(_copy_chart(rel.target_part, target_part.package), RT.CHART)
    return target_part.relate_to(rel.target_part, rel.reltype)


def clone_slide(prs, source):
    """Append a copy of a slide of the same presentation, with its pictures and charts."""
    new_slide = prs.slides.add_slide(source.slide_layout)
    element = new_slide._element
    for child in list(element):
        element.remove(child)
    for key, value in source._element.attrib.items():
        element.set(key, value)
    for child in source._element:
        element.append(copy.deepcopy(child))
    # python-pptx caches the shape tree it read when the slide was created. Drop that cache.
    for cached in ("shapes", "placeholders"):
        new_slide.__dict__.pop(cached, None)
    mapping: dict[str, str] = {}
    for node in element.iter():
        for attribute, value in list(node.attrib.items()):
            if attribute.startswith(R_NAMESPACE):
                if value not in mapping:
                    mapping[value] = _copy_relationship(source.part, new_slide.part, value)
                node.set(attribute, mapping[value])
    return new_slide


def drop_unused_relationships(slide) -> None:
    """Forget pictures and charts the slide no longer shows, so they are not saved."""
    used = {value for node in slide._element.iter() for attribute, value in node.attrib.items()
            if attribute.startswith(R_NAMESPACE)}
    for rid, rel in list(slide.part.rels.items()):
        if rid not in used and rel.reltype not in (RT.SLIDE_LAYOUT, RT.NOTES_SLIDE):
            slide.part.drop_rel(rid)


def delete_slide(prs, slide) -> None:
    id_list = prs.slides._sldIdLst
    for slide_id in list(id_list):
        if prs.part.related_part(slide_id.rId) is slide.part:
            rid = slide_id.rId
            id_list.remove(slide_id)
            prs.part.drop_rel(rid)
            return
    raise ValueError("slide not found")


def move_slide(prs, slide, index: int) -> None:
    id_list = prs.slides._sldIdLst
    for slide_id in list(id_list):
        if prs.part.related_part(slide_id.rId) is slide.part:
            id_list.remove(slide_id)
            id_list.insert(index, slide_id)
            return
    raise ValueError("slide not found")


NOTES_BODY = (
    '<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
    '<p:nvSpPr><p:cNvPr id="{id}" name="Notes"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
    '<p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr>'
    '<p:spPr><a:xfrm><a:off x="685800" y="4400550"/><a:ext cx="5486400" cy="3600450"/></a:xfrm></p:spPr>'
    '<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>'
)


def set_notes(slide, text: str) -> None:
    """Write the speaker notes, adding the notes text box when the notes master has none."""
    notes = slide.notes_slide
    if notes.notes_text_frame is None:
        from pptx.oxml import parse_xml
        tree = notes.shapes._spTree
        next_id = max([int(e.get("id")) for e in tree.iter(qn("p:cNvPr"))] + [1]) + 1
        tree.append(parse_xml(NOTES_BODY.format(id=next_id)))
    notes.notes_text_frame.text = text


def remove_sections(prs) -> None:
    """Drop PowerPoint sections, which would point at deleted slides or miss new ones."""
    for extension in list(prs.part._element.iter(qn("p:ext"))):
        if extension.get("uri") == "{521415D9-36F7-43E2-AB2F-B90AF26B5E84}":
            extension.getparent().remove(extension)


def remove_unused_layouts(prs) -> None:
    for master in prs.slide_masters:
        for layout in list(master.slide_layouts):
            if not layout.used_by_slides:
                master.slide_layouts.remove(layout)


def set_paragraphs(text_frame, specs: list) -> None:
    """Replace the text of each paragraph and keep the formatting of its runs.

    Each item of specs is None (keep the paragraph), a string (one run with the
    formatting of the first run) or a list of strings (one per run, in order).
    Paragraphs beyond the list are removed.
    """
    paragraphs = list(text_frame.paragraphs)
    while len(paragraphs) < len(specs):
        last = paragraphs[-1]._p
        last.addnext(copy.deepcopy(last))
        paragraphs = list(text_frame.paragraphs)
    for index, paragraph in enumerate(paragraphs):
        element = paragraph._p
        if index >= len(specs):
            element.getparent().remove(element)
            continue
        spec = specs[index]
        if spec is None:
            continue
        texts = [spec] if isinstance(spec, str) else list(spec)
        for line_break in element.findall(qn("a:br")):
            element.remove(line_break)
        runs = element.findall(qn("a:r"))
        if not runs:
            paragraph.add_run()
            runs = element.findall(qn("a:r"))
        while len(runs) < len(texts):
            runs[-1].addnext(copy.deepcopy(runs[-1]))
            runs = element.findall(qn("a:r"))
        for run in runs[len(texts):]:
            element.remove(run)
        for run, text in zip(runs, texts):
            run.find(qn("a:t")).text = text

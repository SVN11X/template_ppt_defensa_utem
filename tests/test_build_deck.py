"""Tests of scripts/build_deck.py against the real catalog and the example content."""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_deck  # noqa: E402
from pptx_tools import open_presentation  # noqa: E402

EXAMPLE = ROOT / "content" / "01-defensa.yml"


class FlattenTest(unittest.TestCase):
    def test_lists_are_numbered_from_one(self):
        values = build_deck.flatten({"cifras": [{"valor": 3}, {"valor": "4 cm"}], "oculta": True})
        self.assertEqual(values, {"cifras.1.valor": "3", "cifras.2.valor": "4 cm"})

    def test_missing_list_items_are_detected(self):
        fields = build_deck.Fields({"puntos.1.nombre": "a", "tabla.filas.2.1": "b"})
        self.assertTrue(fields.missing_item("puntos.2.texto"))
        self.assertFalse(fields.missing_item("puntos.1.texto"))
        self.assertTrue(fields.missing_item("tabla.filas.3.1"))
        self.assertFalse(fields.missing_item("titulo"))


class BuildExampleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.tmp.name) / "defensa.pptx"
        cls.warnings, cls.stats = build_deck.build(EXAMPLE, build_deck.TEMPLATE, cls.output)
        cls.content = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
        cls.prs = open_presentation(cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_one_slide_per_entry_and_no_pattern_left(self):
        self.assertEqual(len(self.prs.slides), len(self.content["laminas"]))

    def test_every_marker_is_filled(self):
        with zipfile.ZipFile(self.output) as package:
            for name in package.namelist():
                if re.match(r"ppt/slides/slide\d+\.xml$", name):
                    self.assertNotIn("{{", package.read(name).decode("utf-8"), name)

    def test_backup_slides_are_hidden(self):
        hidden = [s for s in self.prs.slides if s._element.get("show") == "0"]
        expected = [s for s in self.content["laminas"] if s["modelo"].startswith("respaldo-")]
        self.assertEqual(len(hidden), len(expected))

    def test_page_numbers_count_only_visible_slides(self):
        visible = sum(1 for s in self.content["laminas"] if not s["modelo"].startswith("respaldo-"))
        texts = [shape.text_frame.text for shape in self.prs.slides[3].shapes if shape.name == "footer:page"]
        self.assertEqual(texts, [f"04 / {visible:02d}"])

    def test_speaker_script_goes_to_the_notes(self):
        notes = self.prs.slides[3].notes_slide.notes_text_frame.text
        self.assertTrue(notes.startswith("(75 s) "))

    def test_unused_list_items_are_removed(self):
        problema = self.prs.slides[3]
        points = [s for s in problema.shapes if s.name.startswith("item:puntos.")]
        self.assertEqual(len(points), 2 * 3)  # three text boxes and three icons

    def test_the_script_file_is_written(self):
        script = self.output.with_name("guion.md").read_text(encoding="utf-8")
        self.assertIn("## Lámina 4", script)
        self.assertEqual(self.stats["visible_seconds"],
                         sum(int(s.get("segundos", 0)) for s in self.content["laminas"]
                             if not s["modelo"].startswith("respaldo-")))


class ErrorsTest(unittest.TestCase):
    def test_unknown_model_is_an_error(self):
        content = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
        content["laminas"] = [{"modelo": "no-existe"}]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "defensa.yml"
            path.write_text(yaml.safe_dump(content, allow_unicode=True), encoding="utf-8")
            with self.assertRaises(build_deck.BuildError):
                build_deck.build(path, build_deck.TEMPLATE, Path(tmp) / "out.pptx")


if __name__ == "__main__":
    unittest.main()

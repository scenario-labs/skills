import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import ImageChops

SCRIPT = Path(__file__).resolve().parents[2] / "skills/scenario-game-assets/scripts/build_isometric_templates.py"
SPEC = importlib.util.spec_from_file_location("templates", SCRIPT)
templates = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(templates)


class TemplateTests(unittest.TestCase):
    def test_neighbors_share_an_entire_edge(self):
        for shape in ("diamond", "hex"):
            points, steps = templates.geometry(shape)
            for dx, dy in steps:
                shared = set(points) & {(x + dx, y + dy) for x, y in points}
                self.assertEqual(len(shared), 2, (shape, dx, dy))

    def test_regions_partition_base_and_preserve_headroom(self):
        for shape in ("diamond", "hex"):
            for thickness in (0, 32):
                images, _, _ = templates.build(shape, thickness)
                ground, side = images["ground-region"], images["side-region"]
                alpha = images["reference"].getchannel("A")
                self.assertIsNone(ImageChops.multiply(ground, side).getbbox())
                self.assertIsNone(ImageChops.difference(
                    ImageChops.lighter(ground, side), alpha).getbbox())
                self.assertIsNone(ImageChops.subtract(
                    alpha, images["object-region"]).getbbox())
                self.assertLess(images["object-region"].getbbox()[1],
                                ground.getbbox()[1] - 400)

    def test_reproducible_bundle(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            first = templates.write_bundle(Path(a))
            self.assertEqual(first, templates.write_bundle(Path(b)))
            self.assertEqual(len(first["templates"]), 4)
            self.assertEqual(len(list(Path(a).glob("*.png"))), 17)


if __name__ == "__main__":
    unittest.main()

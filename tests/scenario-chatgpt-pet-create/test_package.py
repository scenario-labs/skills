import contextlib
import io
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import synth  # noqa: E402

import pet_build  # noqa: E402
import pet_check  # noqa: E402
import pet_common as pc  # noqa: E402
import pet_package  # noqa: E402
import pet_preview  # noqa: E402


def quiet(fn, argv):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(argv)


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = synth.tmpdir(cls)
        with contextlib.redirect_stdout(io.StringIO()):
            cls.run_dir = synth.make_run(cls.tmp, version=2)
            pet_build.main([str(cls.run_dir)])
            sheet = str(cls.run_dir / "final" / "spritesheet.webp")
            pet_check.main([sheet, "--run", str(cls.run_dir)])
            pet_preview.main(["gif", sheet, "--out-dir", str(cls.run_dir / "previews")])
            pet_package.main(["make", str(cls.run_dir)])
        cls.package = cls.run_dir / "package"

    def test_pet_json(self):
        manifest = pc.read_json(self.package / "blob" / "pet.json")
        self.assertEqual(
            manifest,
            {"id": "blob", "displayName": "Blob", "description": "Blob, an animated pet companion.", "spritesheetPath": "spritesheet.webp"},
        )

    def test_sheet_bytes_are_the_checked_bytes(self):
        original = (self.run_dir / "final" / "spritesheet.webp").read_bytes()
        self.assertEqual((self.package / "blob" / "spritesheet.webp").read_bytes(), original)

    def test_v1_cut_is_rows_0_to_8(self):
        v1 = pc.load_rgba(self.package / "spritesheet-v1.png")
        sheet = pc.load_rgba(self.run_dir / "final" / "spritesheet.webp")
        self.assertEqual(v1.shape[:2], (1872, 1536))
        self.assertTrue(np.array_equal(v1, sheet[:1872]))

    def test_gifs_are_packaged(self):
        self.assertTrue((self.package / "pet.gif").is_file())
        self.assertTrue((self.package / "pet-transparent.gif").is_file())

    def test_refuses_bytes_that_were_not_checked(self):
        other = self.tmp / "other.webp"
        sheet = pc.load_rgba(self.run_dir / "final" / "spritesheet.webp")
        sheet[0, 0] = (1, 2, 3, 255)
        pc.save_webp(sheet, other)
        with self.assertRaises(SystemExit):
            quiet(pet_package.main, ["make", str(self.run_dir), "--sheet", str(other)])

    def test_install_backs_up_and_needs_force(self):
        home = self.tmp / "codex"
        quiet(pet_package.main, ["install", str(self.run_dir), "--codex-home", str(home)])
        installed = home / "pets" / "blob"
        self.assertTrue((installed / "pet.json").is_file())
        self.assertTrue((installed / "spritesheet.webp").is_file())
        with self.assertRaises(SystemExit):
            quiet(pet_package.main, ["install", str(self.run_dir), "--codex-home", str(home)])
        quiet(pet_package.main, ["install", str(self.run_dir), "--codex-home", str(home), "--force"])
        self.assertTrue(list(self.package.glob("backup-blob-*")))


if __name__ == "__main__":
    unittest.main()

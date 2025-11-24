import unittest

from skin_creator import helpers


class TestColorMath(unittest.TestCase):
    def test_lighten_black_to_white(self):
        self.assertEqual(helpers.lighten("#000000", 1.0), "#ffffff")

    def test_lighten_mid_gray(self):
        # Halfway to white should move 0x80 towards 0xFF by half of the distance.
        self.assertEqual(helpers.lighten("#808080", 0.5), "#c0c0c0")

    def test_darken_white_to_black(self):
        self.assertEqual(helpers.darken("#ffffff", 1.0), "#000000")

    def test_darken_mid_gray(self):
        self.assertEqual(helpers.darken("#808080", 0.25), "#606060")


class TestFilenameHelpers(unittest.TestCase):
    def test_ensure_extension_adds_missing(self):
        self.assertEqual(
            helpers.ensure_extension("player-base", "img"),
            "player-base.img",
        )

    def test_ensure_extension_replaces_existing(self):
        self.assertEqual(
            helpers.ensure_extension("player-base.png", "img"),
            "player-base.img",
        )

    def test_apply_prefix_no_existing_dir(self):
        self.assertEqual(
            helpers.apply_prefix("img/player", "player-base.img"),
            "img/player/player-base.img",
        )

    def test_apply_prefix_retains_existing_dir(self):
        self.assertEqual(
            helpers.apply_prefix("img/player", "custom/player-base.img"),
            "custom/player-base.img",
        )


class TestExportHelpers(unittest.TestCase):
    def test_filename_for_export_png(self):
        self.assertEqual(
            helpers.filename_for_export("player-base.img", "PNG"),
            "player-base.png",
        )

    @unittest.skipUnless(helpers.HAS_CAIROSVG, "CairoSVG required for PNG export")
    def test_sprite_bytes_png_mime(self):
        svg = "<svg xmlns=\"http://www.w3.org/2000/svg\"><rect width=\"10\" height=\"10\"/></svg>"
        data, mime = helpers.sprite_bytes(svg, "PNG")
        self.assertEqual(mime, "image/png")
        self.assertTrue(data.startswith(b"\x89PNG"))


if __name__ == "__main__":
    unittest.main()

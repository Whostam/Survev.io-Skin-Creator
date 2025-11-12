import json
import unittest

from skin_creator.export import (
    ExportOpts,
    SPRITE_MODE_CUSTOM,
    build_filenames,
    build_manifest,
)


class TestManifest(unittest.TestCase):
    def setUp(self):
        self.opts = ExportOpts(
            skin_name="Test Skin",
            lore="",
            rarity="2",
            noDropOnDeath=False,
            noDrop=True,
            ghillie=False,
            obstacleType="",
            baseScale=1.0,
            lootBorderOn=True,
            lootBorderName="loot-circle-outer-01",
            lootBorderTint="#ffffff",
            lootScale=0.25,
            soundPickup="clothes_pickup_01",
            ref_ext=".img",
        )
        self.filenames = build_filenames(
            base_id="testskin",
            sprite_mode=SPRITE_MODE_CUSTOM,
            existing_sprite_ids={},
            custom_dirs={"player": "img/player/", "loot": "img/loot/"},
            ext_ref="img",
            loot_border_on=True,
            loot_border_name="loot-circle-outer-01",
            loot_inner_name="loot-circle-inner-01",
        )
        self.ui_tints = {
            "base": "0xfefefe",
            "hand": "0xfefefe",
            "foot": "0xfefefe",
            "backpack": "0x111111",
            "loot": "0xffffff",
            "border": "0xffffff",
        }
        self.export_tints = {
            key: "0xffffff" for key in self.ui_tints
        }

    def test_manifest_contains_expected_sections(self):
        manifest_json = build_manifest(
            ident="outfitTest",
            opts=self.opts,
            filenames=self.filenames,
            ui_tints=self.ui_tints,
            export_tints=self.export_tints,
            sprite_mode=SPRITE_MODE_CUSTOM,
            preview_preset="Standing (default)",
            front_meta={"enabled": False, "pos_x": 0, "pos_y": 0, "aboveHand": False},
            preview_options={"overlayEnabled": True, "overlayAboveFront": True},
        )
        data = json.loads(manifest_json)

        self.assertEqual(data["skin"]["ident"], "outfitTest")
        self.assertEqual(data["skin"]["name"], "Test Skin")
        self.assertTrue(data["skin"]["flags"]["noDrop"])
        self.assertEqual(data["sprites"]["mode"], SPRITE_MODE_CUSTOM)
        self.assertEqual(data["sprites"]["referenceExtension"], ".img")
        self.assertIn("base", data["sprites"]["files"])
        self.assertEqual(data["preview"]["preset"], "Standing (default)")
        self.assertTrue(data["preview"]["overlayEnabled"])
        self.assertTrue(data["preview"]["overlayAboveFront"])
        self.assertEqual(data["tints"]["export"]["base"], "0xffffff")
        self.assertEqual(data["loot"]["borderEnabled"], True)
        self.assertIsNotNone(data["loot"]["borderSprite"])
        self.assertEqual(data["loot"]["scale"], 0.25)
        self.assertIn("front", data)
        self.assertFalse(data["front"]["enabled"])
        self.assertIn("pos", data["front"])


if __name__ == "__main__":
    unittest.main()

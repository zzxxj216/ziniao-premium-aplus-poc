import unittest
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import aplus_api
from image_spec import image_item_parts, module_image_items
from validate import validate_spec


class ImageSpecTests(unittest.TestCase):
    def test_image_item_accepts_desktop_aliases(self):
        self.assertEqual(
            image_item_parts({"desktop": "/d.png", "mobile": "/m.png", "alt_text": "Alt"}, "Fallback"),
            ("/d.png", "/m.png", "Alt"),
        )
        self.assertEqual(
            image_item_parts({"desktop_image": "/d2.png", "mobile_image": "/m2.png"}, "Fallback"),
            ("/d2.png", "/m2.png", "Fallback"),
        )

    def test_module_top_level_desktop_mobile_shorthand(self):
        items = module_image_items({"type": "完整图片", "desktop": "/d.png", "mobile": "/m.png", "alt": "Alt"})
        self.assertEqual(items, [{"image": "/d.png", "mobile": "/m.png", "alt": "Alt"}])

    @patch("validate.image_size")
    @patch("validate.os.path.exists", return_value=True)
    def test_validate_accepts_desktop_mobile_dict(self, _exists, image_size):
        def fake_size(path):
            return (1464, 600) if path == "/d.png" else (600, 450)

        image_size.side_effect = fake_size
        spec = {
            "name": "dual image",
            "modules": [
                {"type": "完整图片", "images": [{"desktop": "/d.png", "mobile": "/m.png", "alt": "Alt"}]},
            ],
        }
        self.assertEqual(validate_spec(spec), [])

    @patch("validate.os.path.exists", return_value=True)
    def test_validate_rejects_missing_desktop_in_dict(self, _exists):
        spec = {"name": "bad", "modules": [{"type": "完整图片", "images": [{"mobile": "/m.png"}]}]}
        errors = validate_spec(spec)
        self.assertTrue(any("缺桌面图 image/desktop" in e for e in errors))

    @patch("aplus_api.resize_cover")
    def test_prepare_full_image_resizes_desktop_and_explicit_mobile_separately(self, resize_cover):
        resize_cover.side_effect = lambda path, w, h: f"{path}|{w}x{h}"
        img, mobile, alt = aplus_api._prepare_image_upload(
            {"desktop": "/desktop.png", "mobile": "/mobile.png", "alt": "Alt"},
            "Fallback",
            True,
            aplus_api.DESKTOP_TARGET["完整图片"],
            aplus_api.MOBILE_TARGET,
            auto_mobile=True,
        )
        self.assertEqual(img, "/desktop.png|1464x600")
        self.assertEqual(mobile, "/mobile.png|600x450")
        self.assertEqual(alt, "Alt")

    @patch("aplus_api.resize_cover")
    def test_prepare_full_image_auto_generates_mobile_from_desktop_when_missing(self, resize_cover):
        resize_cover.side_effect = lambda path, w, h: f"{path}|{w}x{h}"
        _, mobile, _ = aplus_api._prepare_image_upload(
            "/desktop.png",
            "Fallback",
            True,
            aplus_api.DESKTOP_TARGET["完整图片"],
            aplus_api.MOBILE_TARGET,
            auto_mobile=True,
        )
        self.assertEqual(mobile, "/desktop.png|600x450")


if __name__ == "__main__":
    unittest.main()

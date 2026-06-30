import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_full import JS_GALLERY_SEARCH


def _extract_gallery_search_id(html):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1000})
        page.set_content(html)
        handle = page.evaluate_handle(f"() => {{ {JS_GALLERY_SEARCH} }}")
        result = handle.evaluate("(el) => el && el.id")
        browser.close()
        return result


class GallerySearchTests(unittest.TestCase):
    def test_old_seller_central_modal_search_beats_global_search(self):
        html = """
        <style>
          body { margin: 0; font-family: sans-serif; }
          .navbar { height: 90px; background: #101820; color: white; }
          #old-global-search { position: absolute; top: 35px; left: 640px; width: 380px; height: 32px; }
          .modal { position: absolute; top: 125px; left: 40px; width: 1500px; height: 760px; }
          #module-gallery-search { position: absolute; top: 90px; left: 16px; width: 1460px; height: 32px; }
          .tile { position: absolute; top: 170px; left: 40px; width: 440px; height: 260px; }
        </style>
        <div class="navbar">
          amazon seller central
          <input id="old-global-search" placeholder="Search" value="">
        </div>
        <div class="modal" role="dialog" aria-modal="true">
          <h1>Add Module</h1>
          <input id="module-gallery-search" placeholder="Search" value="">
          <div class="tile">Premium Full Image</div>
        </div>
        """
        self.assertEqual(_extract_gallery_search_id(html), "module-gallery-search")


if __name__ == "__main__":
    unittest.main()

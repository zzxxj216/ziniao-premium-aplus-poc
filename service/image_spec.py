"""Helpers for desktop/mobile image items in A+ specs."""


DESKTOP_KEYS = ("image", "desktop", "desktop_image")
MOBILE_KEYS = ("mobile", "mobile_image")
ALT_KEYS = ("alt", "alt_text")


def first_present(data, keys):
    if not isinstance(data, dict):
        return None
    for key in keys:
        value = data.get(key)
        if value:
            return value
    return None


def image_item_parts(item, default_alt=None):
    """Return (desktop_path, mobile_path, alt) for string or dict image items.

    Supported dict keys:
    - desktop image: image | desktop | desktop_image
    - mobile image: mobile | mobile_image
    - alt text: alt | alt_text
    """
    if isinstance(item, dict):
        desktop = first_present(item, DESKTOP_KEYS)
        mobile = first_present(item, MOBILE_KEYS)
        alt = first_present(item, ALT_KEYS) or default_alt
        return desktop, mobile, alt
    return item, None, default_alt


def module_image_items(module):
    """Return module image list, with a single-image shorthand fallback.

    Preferred shape remains:
      {"images": [{"image": "/desktop.png", "mobile": "/mobile.png"}]}

    For one-image modules this also accepts:
      {"image": "/desktop.png", "mobile": "/mobile.png"}
      {"desktop": "/desktop.png", "mobile": "/mobile.png"}
    """
    images = module.get("images")
    if images is not None:
        if isinstance(images, list):
            return images
        return [images]
    desktop = first_present(module, DESKTOP_KEYS)
    mobile = first_present(module, MOBILE_KEYS)
    if desktop or mobile:
        item = {"image": desktop, "mobile": mobile}
        alt = first_present(module, ALT_KEYS)
        if alt:
            item["alt"] = alt
        return [item]
    return []


def has_explicit_mobile(item):
    if isinstance(item, dict):
        return bool(first_present(item, MOBILE_KEYS))
    return False

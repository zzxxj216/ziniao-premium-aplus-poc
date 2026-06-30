"""英文站补测:对比表2 / 视频 / 热点1 / 轮播简单 / 背景图片,各自独立成篇。"""
import json, os, time
from aplus_api import create_aplus

IMG = "/Users/zane/Desktop/dinosaur/A+/ChatGPT Image 2026年6月23日 10_44_19 (1).png"
IMG2 = "/Users/zane/Desktop/dinosaur/A+/ChatGPT Image 2026年6月23日 10_44_19 (2).png"
VIDEO = "/Users/zane/Downloads/mothers_day/5cd32eaf-9009-4844-aec8-fe85132907d3.mp4"
ASINS = ["B0D81DLXSJ", "B0H28WPJ33"]

SPECS = [
    {"tag": "对比表2", "name": "ZZTEST_EN_cmp2_",
     "modules": [{"type": "对比表2", "title": "Compare", "asins": ASINS,
                  "img_titles": ["Ours", "Theirs"], "images": [IMG, IMG2]}]},
    {"tag": "背景图片", "name": "ZZTEST_EN_bg_",
     "modules": [{"type": "背景图片", "images": [IMG], "title": "BG Title",
                  "subtitle": "BG Sub", "body": "Overlay body text."}]},
    {"tag": "轮播简单", "name": "ZZTEST_EN_caro_",
     "modules": [{"type": "轮播", "variant": "简单",
                  "panels": [{"image": IMG, "texts": ["Panel one body"]},
                             {"image": IMG2, "texts": ["Panel two body"]}]}]},
    {"tag": "热点1", "name": "ZZTEST_EN_hs_",
     "modules": [{"type": "热点1", "images": [IMG],
                  "hotspots": [{"title": "Waterproof", "body": "Fully waterproof."},
                               {"title": "Durable", "body": "Fade resistant."}]}]},
    {"tag": "全视频", "name": "ZZTEST_EN_vid_",
     "modules": [{"type": "视频", "video": VIDEO, "title": "Demo video",
                  "body": "Watch it in action."}]},
]


def main():
    store = os.environ.get("ZINIAO_STORE", "XY")
    for s in SPECS:
        spec = {"store": store, "name": s["name"] + time.strftime("%H%M%S"), "modules": s["modules"]}
        try:
            r = create_aplus(spec)
        except Exception as e:
            r = {"ok": False, "error": str(e)}
        print(f"@@@ {s['tag']}: " + json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    main()

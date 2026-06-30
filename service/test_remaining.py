"""批测剩余模块:每个单独成篇 create_aplus,打印结果。"""
import json, os, time
from aplus_api import create_aplus

IMG = "/Users/zane/Desktop/dinosaur/A+/ChatGPT Image 2026年6月23日 10_44_19 (1).png"
ASINS = ["B0D81DLXSJ", "B0H28WPJ33"]

SPECS = [
    {"name": "ZZTEST_hotspot1_" + time.strftime("%H%M%S"),
     "modules": [{"type": "热点1", "images": [IMG]}]},
    {"name": "ZZTEST_hotspot2_" + time.strftime("%H%M%S"),
     "modules": [{"type": "热点2", "images": [IMG], "texts": ["Hotspot title"], "bodies": ["Hotspot body text."]}]},
    {"name": "ZZTEST_cmp1_" + time.strftime("%H%M%S"),
     "modules": [{"type": "对比表1", "asins": ASINS, "images": [IMG, IMG], "img_titles": ["A", "B"], "texts": ["Compare"]}]},
    {"name": "ZZTEST_cmp3_" + time.strftime("%H%M%S"),
     "modules": [{"type": "对比表3", "asins": ASINS, "images": [IMG, IMG], "texts": ["Compare"]}]},
]


def main():
    for spec in SPECS:
        spec["store"] = os.environ.get("ZINIAO_STORE", "XY")
        r = create_aplus(spec)
        print("\n##### " + spec["modules"][0]["type"] + " #####")
        print(json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    main()

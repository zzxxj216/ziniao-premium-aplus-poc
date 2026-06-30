"""精选真机边界测试:7模块满载 / 超长+emoji+特殊+希伯来 / 虚假ASIN。各建一个 ZZTEST 草稿。"""
import json, os, time
from aplus_api import create_aplus

B = "/Users/zane/Desktop/dinosaur/A+/ChatGPT Image 2026年6月23日 10_44_19 (1).png"
B2 = "/Users/zane/Desktop/dinosaur/A+/ChatGPT Image 2026年6月23日 10_44_19 (2).png"
STORE = os.environ.get("ZINIAO_STORE", "XY")

LONG = "A" * 200  # 远超 80 上限,测截断
WEIRD = "Quote\"&<b>tag</b> emoji😀🦖 newline\nend"  # 特殊字符+emoji+换行
HEBREW = "מוצר עמיד למים"  # 希伯来文(RTL)

CASES = [
    ("7模块满载", {"name": "ZZTEST_edge_7mod_" + time.strftime("%H%M%S"), "store": STORE, "modules": [
        {"type": "完整图片", "images": [B], "title": "Banner"},
        {"type": "单图文", "images": [B], "title": "T1", "subtitle": "S1", "body": "B1"},
        {"type": "双图", "images": [B, B2], "texts": ["L", "R"], "bodies": ["bl", "br"]},
        {"type": "四图", "images": [B, B2, B, B2], "texts": ["m", "a", "b", "c", "d"], "bodies": ["1", "2", "3", "4"]},
        {"type": "文本", "title": "Text", "body": "para"},
        {"type": "问答", "texts": ["Q1?", "A1", "Q2?", "A2"]},
        {"type": "技术规格", "texts": ["Spec", "k1", "v1", "k2", "v2"]},
    ]}),
    ("超长+emoji+特殊+希伯来", {"name": "ZZTEST_edge_text_" + time.strftime("%H%M%S"), "store": STORE, "modules": [
        {"type": "单图文", "images": [B], "title": LONG, "subtitle": WEIRD, "body": HEBREW},
    ]}),
    ("虚假ASIN(格式合法)", {"name": "ZZTEST_edge_asin_" + time.strftime("%H%M%S"), "store": STORE, "modules": [
        {"type": "对比表2", "title": "Cmp", "asins": ["B0FAKE00001", "B0FAKE00002"],
         "img_titles": ["A", "B"], "images": [B, B2]},
    ]}),
]


def main():
    for tag, spec in CASES:
        try:
            r = create_aplus(spec)
        except Exception as e:
            r = {"ok": False, "exception": str(e)}
        print(f"@@@ {tag}: " + json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""预检层:提交即校验 spec(不碰浏览器、不建草稿),挡掉素材/结构类错误并给清晰报错。"""
import os
import re
import subprocess

from image_spec import image_item_parts, module_image_items

ASIN_RE = re.compile(r"^[A-Z0-9]{10}$")
VIDEO_EXT = (".mp4", ".mov", ".m4v")

# 每模块规则:img_min=图片最小(w,h);imgs=需要图片张数;video/asins/hotspots/carousel 标记
MODULE_RULES = {
    "完整图片": {"img_min": (1464, 600), "imgs": 1},
    "单图文":   {"img_min": (800, 600), "imgs": 1},
    "双图":     {"img_min": (650, 350), "imgs": 2},
    "四图":     {"img_min": (300, 225), "imgs": 4},
    "文本":     {"imgs": 0},
    "背景图片": {"img_min": (1464, 600), "imgs": 1},
    "问答":     {"imgs": 0},
    "技术规格": {"imgs": 0},
    "视频":     {"video": True},
    "含文本视频": {"video": True},
    "对比表1":  {"asins": True, "img_min": (200, 225)},
    "对比表2":  {"asins": True, "img_min": (300, 225)},
    "对比表3":  {"asins": True, "img_min": (488, 700)},
    "热点1":    {"img_min": (1464, 600), "imgs": 1},
    "热点2":    {"img_min": (1464, 600), "imgs": 1},
    "轮播":     {"carousel": True},
}
CAROUSEL_MAXP = {"简单": 6, "规则": 5, "导航": 5, "视频图像": 6}


def image_size(path):
    """用 sips 读图片像素尺寸,失败返回 None(则跳过尺寸校验,仅查存在)。"""
    try:
        out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
                             capture_output=True, text=True, timeout=15).stdout
        w = h = None
        for line in out.splitlines():
            s = line.strip()
            if s.startswith("pixelWidth:"):
                w = int(s.split(":")[1])
            elif s.startswith("pixelHeight:"):
                h = int(s.split(":")[1])
        return (w, h) if w and h else None
    except Exception:
        return None


def _check_img(errs, tag, path, minwh):
    if not path or not os.path.exists(path):
        errs.append(f"{tag}: 图片不存在 -> {path}"); return
    sz = image_size(path)
    if sz and minwh:
        w, h = sz; mw, mh = minwh
        if w < mw or h < mh:
            errs.append(f"{tag}: 图片 {os.path.basename(path)} 尺寸 {w}x{h} < 最小 {mw}x{mh}")


def _check_video(errs, tag, path):
    if not path or not os.path.exists(path):
        errs.append(f"{tag}: 视频不存在 -> {path}")
    elif not path.lower().endswith(VIDEO_EXT):
        errs.append(f"{tag}: 视频格式应为 mp4 -> {path}")


def _check_image_item(errs, tag, item, minwh):
    desktop, mobile, _ = image_item_parts(item)
    if not desktop:
        errs.append(f"{tag}: 缺桌面图 image/desktop")
    else:
        _check_img(errs, tag, desktop, minwh)
    if mobile:
        _check_img(errs, f"{tag}(移动)", mobile, (600, 450))


def validate_spec(spec):
    """返回错误列表(空=通过)。"""
    errs = []
    if not (spec.get("name") or "").strip():
        errs.append("缺 name(内容描述名称)")
    mods = spec.get("modules")
    if not isinstance(mods, list) or not mods:
        errs.append("缺 modules,或不是非空列表")
        return errs
    if len(mods) > 7:
        errs.append(f"模块数 {len(mods)} 超过 7(亚马逊高级 A+ 上限)")

    for i, m in enumerate(mods):
        t = m.get("type")
        tag = f"模块{i+1}[{t}]"
        rule = MODULE_RULES.get(t)
        if not rule:
            errs.append(f"{tag}: 未知模块类型(支持:{'/'.join(MODULE_RULES)})"); continue

        if rule.get("carousel"):
            variant = m.get("variant", "简单")
            if variant not in CAROUSEL_MAXP:
                errs.append(f"{tag}: 未知 variant '{variant}'(简单/规则/导航/视频图像)"); continue
            panels = m.get("panels") or []
            maxp = CAROUSEL_MAXP[variant]
            if len(panels) < 2:
                errs.append(f"{tag}: 轮播至少 2 个面板,现 {len(panels)}")
            if len(panels) > maxp:
                errs.append(f"{tag}: {variant}轮播面板 {len(panels)} 超上限 {maxp}")
            minwh = (800, 600) if variant == "视频图像" else (1464, 600)
            for pi, p in enumerate(panels):
                desktop, mobile, _ = image_item_parts(p)
                if desktop:
                    _check_img(errs, f"{tag}面板{pi+1}", desktop, minwh)
                    if mobile:
                        _check_img(errs, f"{tag}面板{pi+1}(移动)", mobile, (600, 450))
                elif variant != "视频图像":
                    errs.append(f"{tag}面板{pi+1}: 缺桌面图 image/desktop")
                if variant == "视频图像":
                    if not p.get("video"):
                        errs.append(f"{tag}面板{pi+1}: 视频图像轮播缺 video")
                    else:
                        _check_video(errs, f"{tag}面板{pi+1}", p["video"])
            continue

        if rule.get("video"):
            if not m.get("video"):
                errs.append(f"{tag}: 缺 video(mp4 路径)")
            else:
                _check_video(errs, tag, m["video"])

        if rule.get("asins"):
            asins = m.get("asins") or []
            if not asins:
                errs.append(f"{tag}: 对比表缺 asins(真实 ASIN)")
            for a in asins:
                if not ASIN_RE.match(str(a)):
                    errs.append(f"{tag}: ASIN 格式错 '{a}'(应为 10 位大写字母/数字)")

        imgs = module_image_items(m)
        need = rule.get("imgs")
        if need and len(imgs) < need:
            errs.append(f"{tag}: 需 {need} 张图,只给了 {len(imgs)}")
        for item in imgs:
            _check_image_item(errs, tag, item, rule.get("img_min"))

    return errs


ALT_MAX = 100
TITLE_MAX = 80      # 标题/headline
SUBTITLE_MAX = 40   # 副标题/subheadline
BODY_MAX = 350      # 正文/body(「文本」模块除外,可到 5000)


def _collect_alts(m):
    """收集一个模块里的所有 alt 文本(模块级/alts/图片字典/面板)。"""
    out = []
    if m.get("alt"):
        out.append(m["alt"])
    if m.get("alt_text"):
        out.append(m["alt_text"])
    out += [a for a in (m.get("alts") or []) if a]
    for item in module_image_items(m):
        _, _, alt = image_item_parts(item)
        if alt:
            out.append(alt)
    for p in (m.get("panels") or []):
        if p.get("alt"):
            out.append(p["alt"])
        if p.get("alt_text"):
            out.append(p["alt_text"])
    return out


def spec_warnings(spec):
    """非阻塞提示(不挡创建,字段超长上传时会按 maxlength 截断):
    alt≤100、标题≤80、副标题≤40、正文≤350(「文本」模块正文不限到此)。"""
    warns = []
    for i, m in enumerate(spec.get("modules") or []):
        t = m.get("type")
        tag = f"模块{i+1}[{t}]"
        for a in _collect_alts(m):
            if len(a) > ALT_MAX:
                warns.append(f"{tag}: alt 长 {len(a)} 超 {ALT_MAX},会截断 → '{a[:40]}…'")
        # 标题(keyed title + 各面板若按 [文本,导航文本] 也算标题类)
        if m.get("title") and len(m["title"]) > TITLE_MAX:
            warns.append(f"{tag}: 标题 长 {len(m['title'])} 超 {TITLE_MAX},会截断")
        if m.get("subtitle") and len(m["subtitle"]) > SUBTITLE_MAX:
            warns.append(f"{tag}: 副标题 长 {len(m['subtitle'])} 超 {SUBTITLE_MAX},会截断")
        # 正文(keyed body + bodies[]);「文本」模块正文可到 5000,跳过
        if t != "文本":
            bodies = ([m["body"]] if m.get("body") else []) + list(m.get("bodies") or [])
            for p in (m.get("panels") or []):
                bodies += list(p.get("bodies") or [])
            for b in bodies:
                if len(b) > BODY_MAX:
                    warns.append(f"{tag}: 正文 长 {len(b)} 超 {BODY_MAX},会截断")
    return warns


if __name__ == "__main__":
    import json, sys
    spec = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else {}
    print("errors:", json.dumps(validate_spec(spec), ensure_ascii=False, indent=2))
    print("warnings:", json.dumps(spec_warnings(spec), ensure_ascii=False, indent=2))

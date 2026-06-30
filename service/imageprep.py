"""图片预处理:用 sips【等比缩放(不裁剪)】到目标框内(contain,只缩不放),整图完整保留。结果缓存。"""
import hashlib
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".imgcache")


def image_size(path):
    try:
        out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
                             capture_output=True, text=True, timeout=20).stdout
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


def resize_exact(src, tw, th):
    """固定缩放:直接拉伸到精确 tw×th(不等比、不裁剪、不补边)。
    永远写到缓存,绝不修改源文件。返回新图路径,失败返回原图。"""
    if not src or not os.path.exists(src):
        return src
    sz = image_size(src)
    if not sz:
        return src
    if sz == (tw, th):
        return src
    try:
        os.makedirs(CACHE, exist_ok=True)
        key = hashlib.md5(f"{src}|{os.path.getmtime(src)}|exact{tw}x{th}".encode()).hexdigest()[:16]
        out = os.path.join(CACHE, f"{key}_{tw}x{th}.png")
        if os.path.exists(out):
            return out
        # sips --resampleHeightWidth 高 宽:强制到精确尺寸;--out 写缓存,不动源
        r = subprocess.run(["sips", "--resampleHeightWidth", str(th), str(tw), src, "--out", out],
                           capture_output=True, timeout=40)
        return out if (r.returncode == 0 and os.path.exists(out)) else src
    except Exception:
        return src


# 兼容旧名(create_aplus 调用 resize_cover)
resize_fit = resize_exact
resize_cover = resize_exact


if __name__ == "__main__":
    import sys
    src = sys.argv[1]
    tw, th = int(sys.argv[2]), int(sys.argv[3])
    print("原图:", image_size(src))
    out = resize_cover(src, tw, th)
    print("输出:", out)
    print("输出尺寸:", image_size(out))

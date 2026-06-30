"""
中心程序:create_aplus(spec) —— 按结构化 spec 在 Seller Central 创建高级 A+ 草稿。
封装已跑通的 5 个模块(完整图片/单图文/双图/四图/文本)。识别/选型由 Claude Code 做,本程序只执行创建。

spec 示例:
{
  "store": "XY",
  "name": "My Product A+",
  "modules": [
    {"type": "完整图片", "images": ["/path/a.png"], "texts": ["标题(可选)"], "bodies": ["正文(可选)"]},
    {"type": "单图文",   "images": ["/path/b.png"], "texts": ["标题","副标题"], "bodies": ["正文"]},
    {"type": "双图",     "images": ["/p/c.png","/p/d.png"], "texts": ["标题1","标题2"], "bodies": ["正文1","正文2"]},
    {"type": "四图",     "images": [4 个路径], "texts": ["模块标题","小标题1..4"], "bodies": ["正文1..4"]},
    {"type": "文本",     "texts": ["标题"], "bodies": ["正文"]}
  ]
}
返回: {"ok": bool, "name": str, "url": str, "modules": [每模块结果]}
"""
import os
import time

import yaml
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains

from ziniao_client import ZiniaoClient
from build_full import (open_premium_editor, add_module_v2, add_image_module,
                        click_label, click_contains, both, bmp, JS_NAME_INPUT, JS_IMG_SLOTS, JS_TRIGGERS, DEEP)
from build_generic import JS_TEXT, JS_BODIES
from build_carousel import click_panel
from validate import validate_spec, spec_warnings
from imageprep import resize_cover
from image_spec import image_item_parts, module_image_items, has_explicit_mobile

# 各模块推荐桌面尺寸(上传前自动等比缩放+裁剪到此尺寸);移动区统一 600×450
DESKTOP_TARGET = {
    "完整图片": (1464, 600), "背景图片": (1464, 600), "热点1": (1464, 600), "热点2": (1464, 600),
    "单图文": (800, 600), "双图": (650, 350), "四图": (300, 225),
    "对比表1": (200, 225), "对比表2": (300, 225), "对比表3": (488, 700),
}
CAROUSEL_DT = {"简单": (1464, 600), "规则": (1464, 600), "导航": (1464, 600), "视频图像": (800, 600)}
MOBILE_MODULES = {"完整图片", "背景图片", "热点1", "热点2"}   # 有独立 600×450 移动区
MOBILE_TARGET = (600, 450)

# 模块底部的"样式开关对"(无文字、成对、~80-100×31 的可点击元素):背景黑白 / 图左右布局
JS_STYLE_PAIR = DEEP + """
var out=deepAll(function(e){
  var clk=(e.tagName==='BUTTON'||(e.getAttribute&&e.getAttribute('role')==='button')||(e.getAttribute&&e.getAttribute('tabindex')!=null));
  if(!clk) return false;
  if((e.textContent||'').trim().length>3) return false;
  var cls=''+(e.className&&e.className.baseVal!==undefined?e.className.baseVal:(e.className||''));
  if(/ngstrim|ngs-/.test(cls)) return false;
  var r=e.getBoundingClientRect?e.getBoundingClientRect():{};
  return r.width>=60&&r.width<=140&&r.height>=24&&r.height<=40;
}).sort(function(a,b){return a.getBoundingClientRect().y-b.getBoundingClientRect().y;});
return out;
"""

HERE = os.path.dirname(os.path.abspath(__file__))

# 友好名 → 后台真实模块名(目前支持的 5 个)
MODULE_MAP = {
    "完整图片": "高级完整图片",
    "单图文": "带文本的单张高级图片",
    "双图": "包含文本的高级双图片",
    "四图": "高级四图片和文本",
    "文本": "高级文本",
    "背景图片": "包含文本的高级背景图片",
    "问答": "高级问答",
    "技术规格": "高级技术规格",
    "视频": "高级全视频",
    "含文本视频": "包含文本的高级视频",
    "热点1": "高级热点1",
    "热点2": "高级热点2",
    "对比表1": "高级比较表1",
    "对比表2": "高级比较表2",
    "对比表3": "高级比较表3",
}
JS_BY_PH = DEEP + "var ph=arguments[0];return deepAll(function(n){return (n.tagName==='INPUT'||n.tagName==='TEXTAREA')&&(n.placeholder||'')===ph;}).filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>0;});"


def _fill_by_ph(driver, ph, values, exclude=None):
    """按 placeholder 顺序填(对比表 ASIN/图片标题等);中英双语匹配;排除前面模块遗留空字段。"""
    exclude = exclude or set()
    els = [e for e in driver.execute_script(JS_BY_PH_ANY, both(ph)) if e not in exclude]
    n = 0
    for el, v in zip(els, values or []):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.click(); el.send_keys(bmp(v)); n += 1
        except Exception:
            pass
    return n


def _fill_ph_list(driver, candidates, values, exclude=None):
    """按【显式候选子串列表】填(placeholder 含任一候选,小写匹配);用于 Q&A 分别填问/答。"""
    exclude = exclude or set()
    els = [e for e in driver.execute_script(JS_BY_PH_ANY, candidates) if e not in exclude]
    n = 0
    for el, v in zip(els, values or []):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.click(); el.send_keys(bmp(v)); n += 1
        except Exception:
            pass
    return n


def _prepare_image_upload(item, default_alt, resize_enabled=True, desktop_target=None, mobile_target=None, auto_mobile=False):
    """Resolve and optionally resize one spec image item for the upload dialog."""
    src_d, src_m, alt = image_item_parts(item, default_alt)
    img, img_mobile = src_d, src_m
    if resize_enabled and src_d and desktop_target:
        img = resize_cover(src_d, *desktop_target)
        if src_m and mobile_target:
            img_mobile = resize_cover(src_m, *mobile_target)
        elif auto_mobile and mobile_target:
            img_mobile = resize_cover(src_d, *mobile_target)
    return img, img_mobile, alt


JS_HAS_TXT = DEEP + "var s=arguments[0];return deepAll(function(n){return (n.textContent||'').includes(s);}).length>0;"


JS_HOTSPOT_AREA = DEEP + """
var a=deepAll(function(n){var t=(n.textContent||'').trim();return t==='单击任何位置以添加热点'||t.indexOf('Click anywhere to add')>=0;});
if(!a.length) return null;
var el=a[0],best=a[0],d=0;
while(el&&d<5){var r=el.getBoundingClientRect?el.getBoundingClientRect():{};if(r.width>300&&r.height>150){best=el;break;}el=el.parentElement;d++;}
return best;
"""
JS_EMPTY_INPUTS = DEEP + "return deepAll(function(n){return (n.tagName==='INPUT'||n.tagName==='TEXTAREA')&&!(n.value||'').trim()&&n.id!=='sc-search-field'&&!/搜索|商品描述名称|替代文本/.test((n.placeholder||'')+((n.getAttribute&&n.getAttribute('aria-label'))||''));}).filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>0;});"


def _add_hotspots(driver, hotspots):
    """在热点底图上按坐标铺开放置热点:点位置→填标题/正文→完成。"""
    area = driver.execute_script(JS_HOTSPOT_AREA)
    if not area:
        return 0
    w = area.size.get("width", 1000); cnt = len(hotspots); n = 0
    for i, hs in enumerate(hotspots):
        fx = (i + 1) / (cnt + 1)              # 横向均匀铺开
        dx = int((fx - 0.5) * w * 0.8); dy = 0
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", area)
            ActionChains(driver).move_to_element_with_offset(area, dx, dy).click().perform()
        except Exception:
            continue
        time.sleep(2)
        empties = driver.execute_script(JS_EMPTY_INPUTS)
        for el, v in zip(empties, [hs.get("title", ""), hs.get("body", "")]):
            try:
                el.click(); el.send_keys(bmp(v))
            except Exception:
                pass
        click_label(driver, "完成"); time.sleep(1.5)
        n += 1
    return n


def _upload_video(driver, path):
    """视频:点「添加视频」→ 找 file input(top/iframe)强制可见 → send_keys → 等处理。"""
    cands = []
    for t in both("添加视频"):
        cands = driver.execute_script(JS_TRIGGERS, t)
        if cands:
            break
    for c in cands:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", c); c.click()
        except Exception:
            continue
        time.sleep(3)
        if driver.execute_script("return document.querySelectorAll('input[type=file]').length") or \
           any(True for fr in driver.find_elements(By.TAG_NAME, "iframe")):
            break
    target = None
    driver.switch_to.default_content()
    ins = driver.find_elements(By.CSS_SELECTOR, "input[type=file]")
    if ins:
        target = ins[0]
    else:
        for fr in driver.find_elements(By.TAG_NAME, "iframe"):
            driver.switch_to.default_content()
            try:
                driver.switch_to.frame(fr)
                ins = driver.find_elements(By.CSS_SELECTOR, "input[type=file]")
                if ins:
                    target = ins[0]; break
            except Exception:
                continue
    if not target:
        driver.switch_to.default_content(); return False
    driver.execute_script("arguments[0].style.cssText='display:block!important;visibility:visible!important;opacity:1!important;width:10px;height:10px;position:fixed;left:0;top:0;z-index:99999';", target)
    target.send_keys(path)
    end = time.time() + 180
    while time.time() < end:
        driver.switch_to.default_content()
        if not any(driver.execute_script(JS_HAS_TXT, s) for s in ["正在上传", "正在处理", "上传中", "Uploading", "Processing"]):
            break
        time.sleep(5)
    driver.switch_to.default_content()
    return True
# 图片触发文案:背景图片用"添加背景图片",其余用默认"点击添加图片"
TRIGGER_MAP = {"背景图片": "添加背景图片"}
# 结构类:加行按钮文案(texts 不够时点它加够行)
ROW_BUTTON = {"问答": "添加问题", "技术规格": "添加规格"}
# 轮播变体 → 真实模块名 + 面板上限(简单6;规则/导航5)
CAROUSEL_MAP = {"简单": ("高级、简单的图像轮播", 6),
                "规则": ("高级规则轮播", 5),
                "导航": ("高级导航轮播", 5),
                "视频图像": ("优质视频图像轮播", 6)}


# 按字段名填充:概念 → placeholder/aria 候选子串(小写,中/英双语)
# 用完整 placeholder 避免子串误命中(如 headline 命中 subheadline)
PLACEHOLDERS = {
    "title":     ["输入标题文本", "enter headline text"],
    "subtitle":  ["输入子标题文本", "enter subheadline text"],
    "nav":       ["输入导航文本", "enter navigation text"],
    "img_title": ["输入图片标题文本", "enter image title"],
    "panel_text": ["输入您的文本", "enter your text"],
}
JS_BY_PH_ANY = DEEP + """
var subs=arguments[0];
return deepAll(function(n){
  if(n.tagName!=='INPUT'&&n.tagName!=='TEXTAREA') return false;
  if((n.value||'').trim()) return false;
  var ph=((n.placeholder||'')+' '+((n.getAttribute&&n.getAttribute('aria-label'))||'')).toLowerCase();
  if(!ph.trim()) return false;
  for(var i=0;i<subs.length;i++){ if(ph.indexOf((''+subs[i]).toLowerCase())>=0) return true; }
  return false;
}).filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>0;});
"""
# 所有可见空输入框(用于"本模块开始前已存在的空字段"快照,后续填充排除它们)
JS_ALL_EMPTY = DEEP + "return deepAll(function(n){return (n.tagName==='INPUT'||n.tagName==='TEXTAREA')&&!(n.value||'').trim()&&n.id!=='sc-search-field';}).filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>0;});"


def _fill_field(driver, concept, values, exclude=None):
    """按字段名(概念)填:body 走 Draft.js,其余按 placeholder 候选(双语)匹配。排除前面模块遗留空字段。"""
    exclude = exclude or set()
    if not isinstance(values, list):
        values = [values]
    if concept == "body":
        els = [e for e in driver.execute_script(JS_BODIES) if not (e.text or "").strip() and e not in exclude]
    else:
        els = [e for e in driver.execute_script(JS_BY_PH_ANY, PLACEHOLDERS.get(concept, [concept])) if e not in exclude]
    n = 0
    for el, v in zip(els, values):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.click(); el.send_keys(bmp(v)); n += 1
        except Exception:
            pass
    return n


def _fill_texts(driver, texts, exclude=None):
    exclude = exclude or set()
    els = [e for e in driver.execute_script(JS_TEXT) if e not in exclude]   # 排除前面模块遗留的空字段
    n = 0
    for el, t in zip(els, texts or []):
        try:
            ml = el.get_attribute("maxlength")
            v = t[:int(ml)] if (ml and ml.isdigit()) else t
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.click(); el.send_keys(bmp(v)); n += 1
        except Exception:
            pass
    return n


def _fill_bodies(driver, bodies, exclude=None):
    exclude = exclude or set()
    els = [e for e in driver.execute_script(JS_BODIES) if not (e.text or "").strip() and e not in exclude]
    n = 0
    for el, t in zip(els, bodies or []):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.click(); el.send_keys(bmp(t)); n += 1
        except Exception:
            pass
    return n


JS_STYLE_BY_WIDTH = DEEP + """
var wmin=arguments[0], wmax=arguments[1];
return deepAll(function(e){
  var clk=(e.tagName==='BUTTON'||(e.getAttribute&&e.getAttribute('role')==='button')||(e.getAttribute&&e.getAttribute('tabindex')!=null));
  if(!clk) return false;
  if((e.textContent||'').trim().length>3) return false;   // 无文字(排除"保存为草稿"等)
  var cls=''+(e.className&&e.className.baseVal!==undefined?e.className.baseVal:(e.className||''));
  if(/ngstrim|ngs-/.test(cls)) return false;
  var r=e.getBoundingClientRect?e.getBoundingClientRect():{};
  return r.width>=wmin&&r.width<=wmax&&r.height>=24&&r.height<=40;
}).sort(function(a,b){return a.getBoundingClientRect().y-b.getBoundingClientRect().y;});
"""


def _style_index(module_type, choice, kind="layout"):
    """把 spec 里的样式值翻译成按钮索引.

    layout:
      - 单图文/双图/背景图片: 图右=0, 图左=1
      - 技术规格: 单表=0, 两表=1
    color:
      - 问答/背景图: 白=0, 黑=1
    """
    if choice is None:
        return None
    raw = str(choice).strip().lower()
    if kind == "layout":
        if module_type == "技术规格":
            if raw in ("两表", "双表", "右", "right", "2", "double", "双列", "两列"):
                return 1
            if raw in ("单表", "左", "left", "1", "single", "单列", "一列"):
                return 0
        if raw in ("图左", "左", "left", "图片在左", "左图右文", "左文右图"):
            return 1
        if raw in ("图右", "右", "right", "图片在右", "文左图右", "文右图左"):
            return 0
    if kind == "color":
        if raw in ("黑", "black", "dark", "深色", "黑底", "黑色"):
            return 1
        if raw in ("白", "white", "light", "浅色", "白底", "白色"):
            return 0
    return None


def _pick_style_pair(els):
    if len(els) < 2:
        return None
    ordered = sorted(els, key=lambda e: (e.rect["y"], e.rect["x"]))
    best = None
    best_y = -1
    for i in range(len(ordered) - 1):
        a, b = ordered[i], ordered[i + 1]
        ay, by = a.rect["y"], b.rect["y"]
        if abs(ay - by) > 12:
            continue
        y = max(ay, by)
        if y >= best_y:
            best = (a, b)
            best_y = y
    return best or tuple(ordered[-2:])


def _set_style(driver, wmin, wmax, index):
    """按宽度锁定某类样式开关对(布局/背景/表格),点第 index 个。"""
    els = driver.execute_script(JS_STYLE_BY_WIDTH, wmin, wmax)
    pair = _pick_style_pair(els)
    if pair:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", pair[index])
            pair[index].click()
            return True
        except Exception:
            pass
    return False


def _set_style_ranges(driver, ranges, index):
    for wmin, wmax in ranges:
        if _set_style(driver, wmin, wmax, index):
            return True
    return False


def _cleanup_session(z, driver=None, browser_oauth=None):
    """无论成功/失败都尽量收尾,避免下一次任务撞到旧会话/旧店铺窗口。"""
    if driver is not None:
        try:
            driver.quit()
        except Exception:
            pass
    if browser_oauth:
        try:
            z.close_store(browser_oauth)
        except Exception:
            pass
    try:
        z.exit_client()
    except Exception:
        try:
            z.kill_client()
        except Exception:
            pass


def _set_name(driver, name):
    el = None; end = time.time() + 15
    while time.time() < end and not el:
        el = driver.execute_script(JS_NAME_INPUT); time.sleep(1)
    if not el:
        return False
    try: driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    except Exception: pass
    try: el.click()
    except Exception: pass
    el.send_keys(bmp(name))
    driver.execute_script("arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                          "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));"
                          "try{arguments[0].blur();}catch(e){}", el)
    return (driver.execute_script("return arguments[0].value", el) or "").strip() != ""


def create_aplus(spec, cfg_path=None):
    # 预检:不合格直接返回,不启动浏览器(快速失败 + 清晰报错)
    errs = validate_spec(spec)
    if errs:
        return {"ok": False, "validation_errors": errs, "name": spec.get("name"), "modules": []}
    warnings = spec_warnings(spec)   # 非阻塞提示(如 alt 超 100 会截断)
    cfg_path = cfg_path or os.path.join(HERE, "config.yaml")
    with open(cfg_path) as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    results = []
    z.download_driver(); z.kill_client(); z.start_client()
    driver = None
    browser_oauth = None
    try:
        if not z.wait_ready(90):
            return {"ok": False, "error": "控制 API 未就绪"}
        z.update_core()
        store = z.store_by_name(spec.get("store") or os.environ.get("ZINIAO_STORE", "XY"))
        browser_oauth = store.get("browserOauth")
        driver = z.attach(z.open_store(browser_oauth)); driver.implicitly_wait(8)

        open_premium_editor(driver)
        named = _set_name(driver, spec["name"])  # 名称提前设(编辑器一开就有名称框,避开传视频后被遮挡)
        for i, m in enumerate(spec["modules"]):
            # 本模块开始前【已存在的空字段/空图位】(属于前面模块)→ 本模块所有填充/传图都排除,避免串模块
            excl = set(driver.execute_script(JS_ALL_EMPTY))
            excl_body = set(driver.execute_script(JS_BODIES))
            excl_trig = set()
            for tw in ("点击添加图片", "添加背景图片"):
                for c in both(tw):
                    for e in driver.execute_script(JS_TRIGGERS, c):
                        excl_trig.add(e)
            # 轮播:per-panel(逐面板点标签→传图→填文);variant=简单/规则/导航
            if m["type"] == "轮播":
                variant = m.get("variant", "简单")
                cmod, maxp = CAROUSEL_MAP.get(variant, CAROUSEL_MAP["简单"])
                # 加本轮播前,已存在的面板标签(属于前一个轮播)→ click_panel 排除,避免跨轮播串号
                pre_panel = set(driver.find_elements(By.XPATH,
                    '//*[starts-with(normalize-space(.),"面板(") or starts-with(normalize-space(.),"PANEL (")]'))
                added = add_module_v2(driver, cmod); time.sleep(3)
                if m.get("title"):                       # 模块标题(输入标题文本,填一次,排除前模块空框)
                    _fill_texts(driver, [m["title"]], exclude=excl)
                pres = []
                for n, panel in enumerate((m.get("panels") or [])[:maxp], 1):
                    # 点面板标签,重试到图位出现(加固偶发漏面板)
                    ok_slot = False
                    for _ in range(3):
                        click_panel(driver, n, exclude=pre_panel)   # 只点当前轮播的面板
                        end = time.time() + 10
                        while time.time() < end:
                            if [e for e in driver.execute_script(JS_IMG_SLOTS) if e not in excl_trig]:
                                ok_slot = True; break
                            time.sleep(1)
                        if ok_slot:
                            break
                    ai_gen = bool(m.get("ai_generated") or panel.get("ai_generated"))
                    p_alt = panel.get("alt") or panel.get("alt_text") or m.get("alt") or spec["name"]
                    src_d, _, _ = image_item_parts(panel, p_alt)
                    dt = CAROUSEL_DT.get(variant, (1464, 600))
                    img, img_mobile, alt = _prepare_image_upload(
                        panel, p_alt, m.get("resize", True), dt,
                        MOBILE_TARGET if variant != "视频图像" else dt,
                        auto_mobile=(variant != "视频图像")
                    )
                    okimg = add_image_module(driver, img, alt, n, ai_disclose=ai_gen, exclude_triggers=excl_trig, img_mobile=img_mobile) if (src_d and ok_slot) else False
                    okvid = _upload_video(driver, panel["video"]) if panel.get("video") else None  # 视频图像轮播每面板视频
                    # 规则/导航:texts 按 [面板文本, 导航文本] 顺序;简单:[正文];均排除前模块空框
                    ftp = _fill_texts(driver, panel.get("texts"), exclude=excl)
                    fbp = _fill_bodies(driver, panel.get("bodies"), exclude=excl_body)
                    pres.append({"panel": n, "image": okimg, "video": okvid, "texts": ftp, "bodies": fbp})
                results.append({"type": "轮播", "variant": variant, "ok": added, "panels": pres})
                continue

            real = MODULE_MAP.get(m["type"])
            if not real:
                results.append({"type": m["type"], "ok": False, "error": "未支持的模块类型"}); continue
            added = add_module_v2(driver, real); time.sleep(2)
            # 结构类:先加够行(问答/技术规格);计数排除前模块空字段
            row_btn = ROW_BUTTON.get(m["type"])
            if row_btn and m.get("texts"):
                need = len(m["texts"])
                for _ in range(12):
                    if len([e for e in driver.execute_script(JS_TEXT) if e not in excl]) >= need:
                        break
                    if not click_contains(driver, row_btn, 6):
                        break
                    time.sleep(1.2)
            keyed = {}
            if m["type"] == "问答":
                # Q&A 开头有个无 placeholder 的字段,按顺序填会错位 → 按 placeholder 分别填问/答
                texts = m.get("texts") or []
                qn = _fill_ph_list(driver, ["enter question", "输入问题", "问题"], texts[0::2], exclude=excl)
                an = _fill_ph_list(driver, ["enter answer", "输入回答", "回答"], texts[1::2], exclude=excl)
                ft = qn + an
                fb = 0
            else:
                # 按字段名填充(优先,双语 placeholder,比 positional 更稳;排除前模块空框)
                for concept in ("title", "subtitle", "nav", "img_title", "panel_text"):
                    if m.get(concept) is not None:
                        keyed[concept] = _fill_field(driver, concept, m[concept], exclude=excl)
                if m.get("body") is not None:
                    keyed["body"] = _fill_field(driver, "body", m["body"], exclude=excl_body)
                # positional 兼容(填剩余空字段)
                ft = _fill_texts(driver, m.get("texts"), exclude=excl)
                fb = _fill_bodies(driver, m.get("bodies"), exclude=excl_body)
                # 对比表:ASIN / 图片标题
                if m.get("asins"):
                    _fill_by_ph(driver, "输入ASIN", m["asins"], exclude=excl)
                if m.get("img_titles"):
                    _fill_by_ph(driver, "输入图片标题文本", m["img_titles"], exclude=excl)
            # 再传图(背景图片用专属触发文案;排除前模块空图位)
            trigger = TRIGGER_MAP.get(m["type"], "点击添加图片")
            imgs = module_image_items(m)
            alts = m.get("alts") or []
            mod_alt = m.get("alt")                 # 模块级 alt 兜底
            up = 0
            mobile_up = 0
            ai_gen = bool(m.get("ai_generated"))   # AI 生成图需勾披露
            for j, item in enumerate(imgs):
                avail = [e for c in both(trigger) for e in driver.execute_script(JS_TRIGGERS, c) if e not in excl_trig]
                if not avail:
                    break
                default_alt = (alts[j] if j < len(alts) else None) or mod_alt or spec["name"]
                src_d, _, _ = image_item_parts(item, default_alt)
                img, img_mobile, alt = _prepare_image_upload(
                    item, default_alt, m.get("resize", True),
                    DESKTOP_TARGET.get(m["type"]),
                    MOBILE_TARGET if m["type"] in MOBILE_MODULES else DESKTOP_TARGET.get(m["type"]),
                    auto_mobile=(m["type"] in MOBILE_MODULES)
                )
                if add_image_module(driver, img, alt, f"{i}.{j}", trigger_text=trigger, ai_disclose=ai_gen, exclude_triggers=excl_trig, img_mobile=img_mobile):
                    up += 1
                    if has_explicit_mobile(item):
                        mobile_up += 1
            # 视频(标准 file input,非拖拽)
            vid = _upload_video(driver, m["video"]) if m.get("video") else None
            # 热点:在底图上按坐标放置热点 + 填标题/正文
            hs_n = _add_hotspots(driver, m["hotspots"]) if m.get("hotspots") else None
            # 最后设样式开关(等渲染稳定);布局(div≈100)与 字体颜色/背景(button≈80)可独立设
            time.sleep(1.5)
            styled = {}
            if m.get("layout"):
                idx = _style_index(m["type"], m["layout"], "layout")
                if idx is not None:
                    styled["layout"] = _set_style_ranges(driver, [(90, 125), (60, 140)], idx)
            colorchoice = m.get("font_color") or m.get("background")
            if colorchoice:
                idx = _style_index(m["type"], colorchoice, "color")
                if idx is not None:
                    styled["color"] = _set_style_ranges(driver, [(70, 95), (60, 95)], idx)
            results.append({"type": m["type"], "ok": added, "images": up, "mobile_images": mobile_up, "texts": ft, "bodies": fb,
                            "keyed": (keyed or None), "video": vid, "hotspots": hs_n, "styled": (styled or None)})

        if not named:  # 提前没设上则末尾兜底
            named = _set_name(driver, spec["name"])
        saved = click_label(driver, "保存为草稿")
        time.sleep(8)
        body = driver.execute_script("return document.body?document.body.innerText:''") or ""
        url = driver.current_url
        saved_ok = bool(saved) and "/content/new/" not in url and "/content/" in url  # 语言无关:存后 url 变成内容ID
        return {"ok": saved_ok,
                "name": spec["name"], "store": store.get("browserName"),
                "url": url, "named": named, "modules": results,
                "warnings": (warnings or None),
                "validation_failed": ("验证失败" in body) or ("Validation failed" in body)}
    except Exception as e:
        return {"ok": False, "error": str(e), "modules": results}
    finally:
        _cleanup_session(z, driver, browser_oauth)


if __name__ == "__main__":
    # 自测:一个完整图片模块
    demo = {
        "store": os.environ.get("ZINIAO_STORE", "XY"),
        "name": "ZZTEST_api_" + time.strftime("%H%M%S"),
        "modules": [
            {"type": "视频",
             "video": "/Users/zane/Downloads/mothers_day/5cd32eaf-9009-4844-aec8-fe85132907d3.mp4",
             "texts": ["Watch how it works"],
             "bodies": ["See our dinosaur name labels in action."]},
        ],
    }
    import json
    print(json.dumps(create_aplus(demo), ensure_ascii=False, indent=2))

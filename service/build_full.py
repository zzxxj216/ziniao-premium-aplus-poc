"""
整文件夹跑通:把 <folder>/A+/*.png 每张图建成一个「高级完整图片」模块,合成一篇高级A+草稿。
用法: python build_full.py /Users/zane/Desktop/dinosaur
高级A+单篇最多 7 模块,超出则取前 7(选型本应由 Claude Code 决定,这里仅为跑通)。
"""
import glob
import os
import sys
import time

import yaml
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ziniao_client import ZiniaoClient

HERE = os.path.dirname(os.path.abspath(__file__))
EDITOR_URL = "https://sellercentral.amazon.com/enhanced-content/content-manager/workflow/ebc-premium/content/new/edit"
MODULE = "高级完整图片"
MAX_MODULES = 7

DEEP = """
function deepAll(test){const acc=[];function walk(root){let ns;try{ns=root.querySelectorAll('*');}catch(e){return;}
ns.forEach(n=>{try{if(test(n))acc.push(n);}catch(e){}
if(n.shadowRoot)walk(n.shadowRoot);
if(n.tagName==='IFRAME'){try{if(n.contentDocument)walk(n.contentDocument);}catch(e){}}});}
walk(document);return acc;}
"""

# 中→英 UI 字符串 / 模块名(英文站从真实英文 UI 抓取,2026-06 XY 美国站)
TR = {
    # 导航 / 动作
    "开始创建": "Start creating A+ content", "创建 高级": "Create Premium A+",
    "添加模块": "Add Module", "保存为草稿": "Save as draft", "添加": "Add", "完成": "Done",
    "添加问题": "Add question", "添加规格": "Add specification",
    "添加视频": "Add Video", "添加背景图片": "Add background image", "取消": "Cancel",
    # 字段 / 标签 / 对话框
    "商品描述名称": "Content name", "拖到这里": "Drag image here",
    "点击添加图片": "Click to add image", "替代文本": "alt text", "搜索": "Search",
    "正在上传": "Uploading", "单击任何位置以添加热点": "Click anywhere to add",
    "面板": "Panel", "输入ASIN": "Enter ASIN", "输入图片标题文本": "image title",
    "输入导航文本": "navigation", "输入您的文本": "your text",
    # 19 个模块名
    "高级完整图片": "Premium Full Image", "带文本的单张高级图片": "Premium Single Image with Text",
    "包含文本的高级双图片": "Premium Dual Images with Text", "高级四图片和文本": "Premium Four Images & Text",
    "高级文本": "Premium Text", "包含文本的高级背景图片": "Premium Background Image with Text",
    "高级问答": "Premium Q&A", "高级技术规格": "Premium Technical Specifications",
    "高级、简单的图像轮播": "Premium Simple Image Carousel", "高级规则轮播": "Premium Regimen Carousel",
    "高级导航轮播": "Premium Navigation Carousel", "优质视频图像轮播": "Premium Video Image Carousel",
    "高级全视频": "Premium Full Video", "包含文本的高级视频": "Premium Video with Text",
    "高级比较表1": "Premium Comparison Table 1", "高级比较表2": "Premium Comparison Table 2",
    "高级比较表3": "Premium Comparison Table 3", "高级热点1": "Premium Hotspots 1",
    "高级热点2": "Premium Hotspots 2",
}


def both(s):
    """返回 [中文, 英文] 候选(无翻译则只中文),用于双语匹配。"""
    e = TR.get(s)
    return [s, e] if e else [s]


def bmp(s):
    """剥掉非 BMP 字符(emoji 等):chromedriver send_keys 只支持 BMP,否则整段抛错被跳过。"""
    return "".join(c for c in str(s) if ord(c) <= 0xFFFF)


JS_NAME_INPUT = DEEP + """
function inner(h){if(!h)return null;if(h.tagName==='INPUT')return h;
if(h.shadowRoot){var i=h.shadowRoot.querySelector('input');if(i)return i;}
return h.querySelector?h.querySelector('input'):null;}
var hosts=deepAll(n=>{var l=(n.getAttribute&&(n.getAttribute('label')||n.getAttribute('aria-label')||''))||'';return l.includes('商品描述名称')||l.includes('Content name');});
for(var k=0;k<hosts.length;k++){var i=inner(hosts[k]);if(i)return i;}
return null;
"""
JS_ZONES = DEEP + "return deepAll(n=>{var t=(n.textContent||'');return t.includes('拖到这里')||t.includes('Drag image here');}).sort((a,b)=>a.textContent.length-b.textContent.length);"
# 穿透 shadow 找所有可见"点击添加图片"图位(轮播等多图位在 shadow 里,selenium xpath 找不全)
JS_IMG_SLOTS = DEEP + "return deepAll(function(n){var t=(n.textContent||'').trim();return t==='点击添加图片'||t==='Click to add image';}).filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>0&&r.height>0;});"
# 通用图片触发器(按文案 contains 找,默认"点击添加图片";背景图片用"添加背景图片")
JS_TRIGGERS = DEEP + "var t=arguments[0];return deepAll(function(n){var x=(n.textContent||'').trim();return x.indexOf(t)>=0&&x.length<=t.length+4;}).filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>0&&r.height>0;});"
JS_INJECT = "var i=document.createElement('input');i.type='file';i.id='__sel_up__';i.style.cssText='position:fixed;left:0;top:0;opacity:0;z-index:99999';document.body.appendChild(i);return i;"
JS_DROP = DEEP + """
var input=document.getElementById('__sel_up__');var target=arguments[0];
if(!input||!input.files.length)return 'no-file';
var dt=new DataTransfer();dt.items.add(input.files[0]);
['dragenter','dragover','drop'].forEach(t=>target.dispatchEvent(new DragEvent(t,{bubbles:true,cancelable:true,composed:true,dataTransfer:dt})));
return 'dropped';
"""
JS_ALTS = DEEP + """
var alt=(arguments[0]||'A+ image').slice(0,100);var n=0;
deepAll(el=>el.tagName==='INPUT'&&((el.placeholder||'').includes('替代文本')||(el.placeholder||'').toLowerCase().includes('alt text'))).forEach(function(el){
if((el.value||'').trim())return;
var set=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el),'value').set;
set.call(el,alt);el.dispatchEvent(new Event('input',{bubbles:true}));
el.dispatchEvent(new Event('change',{bubbles:true}));n++;});
return n;
"""
JS_CLICK = DEEP + """
var label=arguments[0].replace(/\\s/g,'');
function lbl(n){var l=(n.getAttribute&&(n.getAttribute('label')||n.getAttribute('aria-label')))||'';return l.replace(/\\s/g,'');}
var c=deepAll(n=>{var t=(n.textContent||'').replace(/\\s/g,'');var ok=(n.tagName==='BUTTON'||n.tagName==='KAT-BUTTON'||n.tagName==='A'||(n.getAttribute&&n.getAttribute('role')==='button'));return ok&&!n.disabled&&(lbl(n)===label||t===label);});
if(c.length){c[c.length-1].click();return true;}return false;
"""
JS_HAS = DEEP + "var s=arguments[0];return deepAll(n=>(n.textContent||'').includes(s)).length>0;"
JS_GET_ALTS = DEEP + "return deepAll(el=>el.tagName==='INPUT'&&((el.placeholder||'').includes('替代文本')||(el.placeholder||'').toLowerCase().includes('alt text'))&&!((el.value||'').trim()));"
# AI 披露勾选框:checkbox 类元素,自身或祖先(<=5层)文本匹配 AI/生成式/披露
JS_AI_DISCLOSE = DEEP + """
var re=/generat|created using|ai-generated|ai generated|生成式|人工智能|disclos|披露|using ai|created with ai/i;
var cks=deepAll(function(n){var tag=n.tagName||'';return (tag==='INPUT'&&n.type==='checkbox')||tag==='KAT-CHECKBOX'||(n.getAttribute&&n.getAttribute('role')==='checkbox');});
for(var i=0;i<cks.length;i++){
  var n=cks[i],r=n.getBoundingClientRect&&n.getBoundingClientRect(); if(!(r&&r.width>0))continue;
  var hit=false,lab=(n.getAttribute&&(n.getAttribute('label')||n.getAttribute('aria-label')))||'';
  if(re.test(lab))hit=true;
  var p=n,d=0; while(p&&d<5&&!hit){ if(re.test(p.textContent||''))hit=true; p=p.parentElement; d++; }
  if(hit)return n;
}
return null;
"""
JS_CLICK_CONTAINS = DEEP + """
var s=arguments[0].replace(/\\s/g,'');
function blob(n){var l=(n.getAttribute&&(n.getAttribute('label')||n.getAttribute('aria-label')))||'';return (l+' '+(n.textContent||'')).replace(/\\s/g,'');}
var c=deepAll(function(n){var ok=(n.tagName==='BUTTON'||n.tagName==='KAT-BUTTON'||n.tagName==='A'||(n.getAttribute&&n.getAttribute('role')==='button'));return ok&&!n.disabled&&blob(n).indexOf(s)>=0;});
if(c.length){c[0].click();return true;}return false;
"""
# 模块库磁贴:textContent 包含模块名、且很"具体"(长度接近模块名,排除外层容器)
JS_TILES = DEEP + """
var m=arguments[0].replace(/\\s/g,'');
return deepAll(function(n){var t=(n.textContent||'').replace(/\\s/g,'');return t.indexOf(m)>=0;})
  .sort(function(a,b){return a.textContent.length-b.textContent.length;});
"""
# 模块库搜索框:限定在 Add Module 弹窗/模块库容器内,避免旧版页面误填顶部全局搜索框。
JS_GALLERY_SEARCH = DEEP + """
function visible(n){
  var r=n.getBoundingClientRect&&n.getBoundingClientRect();
  return !!(r&&r.width>0&&r.height>0);
}
function ident(n){
  var cls=n.className&&n.className.baseVal!==undefined?n.className.baseVal:(n.className||'');
  var attrs='';
  try{attrs=[n.id||'',cls,n.getAttribute('role')||'',n.getAttribute('aria-label')||'',n.getAttribute('data-testid')||''].join(' ');}catch(e){}
  return attrs;
}
function parentOf(n){
  if(n.parentElement) return n.parentElement;
  var root=n.getRootNode&&n.getRootNode();
  return root&&root.host?root.host:null;
}
function isGlobalChrome(n){
  return /ngstrim|sc-search-field|navbar|nav-|masthead|header|global-search|sellercentral-search/i.test(ident(n));
}
function galleryAncestor(n){
  var p=n,d=0;
  while(p&&d<14){
    if(p.tagName==='BODY'||p.tagName==='HTML') return null;
    if(isGlobalChrome(p)) return null;
    var r=p.getBoundingClientRect&&p.getBoundingClientRect();
    var blob='';
    try{blob=(ident(p)+' '+(p.textContent||'')).replace(/\\s+/g,' ');}catch(e){}
    var role=(p.getAttribute&&p.getAttribute('role'))||'';
    var aria=(p.getAttribute&&p.getAttribute('aria-modal'))||'';
    var hasTitle=/Add Module|添加模块/.test(blob);
    var hasTile=/Premium|高级|Image|图片|Comparison|比较|对比|Background|背景|Text|文本|Video|视频|Carousel|轮播|Question|问答|Specification|规格/i.test(blob);
    if(hasTitle&&(role==='dialog'||aria==='true'||/modal|dialog|overlay|kat-modal|ReactModal/i.test(ident(p)))) return p;
    if(hasTitle&&hasTile&&r&&r.width>500&&r.height>250) return p;
    p=parentOf(p); d++;
  }
  return null;
}
var inputs=deepAll(function(n){
  if(n.tagName!=='INPUT') return false;
  var ph=(n.placeholder||'').trim();
  if(ph!=='搜索'&&ph!=='Search') return false;
  if(!visible(n)) return false;
  if(isGlobalChrome(n)) return false;
  return true;
});
var scoped=inputs.filter(function(n){return !!galleryAncestor(n);});
scoped.sort(function(a,b){return a.getBoundingClientRect().top-b.getBoundingClientRect().top;});
if(scoped.length) return scoped[0];
var fallback=inputs.filter(function(n){
  var r=n.getBoundingClientRect();
  return r.top>120&&r.width>300;
});
fallback.sort(function(a,b){return a.getBoundingClientRect().top-b.getBoundingClientRect().top;});
return fallback.length?fallback[0]:null;
"""
# 从给定元素向上找到"可点击卡片"祖先并点击(磁贴标题常在子元素里,需点卡片才触发添加)
JS_CLICK_ANCESTOR = """
var el=arguments[0]; var p=el, best=el, d=0;
while(p&&d<7){
  var st=null; try{st=getComputedStyle(p);}catch(e){}
  if(p.tagName==='BUTTON'||p.tagName==='A'||(p.getAttribute&&p.getAttribute('role')==='button')||(st&&st.cursor==='pointer')){best=p;break;}
  p=p.parentElement; d++;
}
try{best.scrollIntoView({block:'center'});}catch(e){}
best.click(); return true;
"""


def click_label(driver, label, t=25):
    end = time.time() + t
    while time.time() < end:
        for cand in both(label):           # 中英都试
            if driver.execute_script(JS_CLICK, cand):
                return True
        time.sleep(1.5)
    return False


CM_URL = "https://sellercentral.amazon.com/enhanced-content/content-manager"


def safe_get(driver, url):
    """导航,自动吃掉 beforeunload『未保存』确认框。"""
    from selenium.common.exceptions import UnexpectedAlertPresentException
    try:
        driver.get(url)
    except UnexpectedAlertPresentException:
        try: driver.switch_to.alert.accept()
        except Exception: pass
        driver.get(url)
    try:
        driver.switch_to.alert.accept()
    except Exception:
        pass


def _has(driver, s):
    """页面是否出现某文案(中英都查)。"""
    for cand in both(s):
        if driver.execute_script(JS_HAS, cand):
            return True
    return False


def click_contains(driver, s, t=30):
    """穿透 shadow,按 label/文本【包含】点击(兼容 kat-button)。"""
    end = time.time() + t
    while time.time() < end:
        for cand in both(s):               # 中英都试
            if driver.execute_script(JS_CLICK_CONTAINS, cand):
                return True
        time.sleep(1.5)
    return False


def open_premium_editor(driver):
    """一步步走 UI 进入高级 A+ 编辑器(不深链),按钮用 kat-button 兼容点击。"""
    last = "进入编辑器失败"
    for attempt in range(3):                       # 整体重试:吃掉瞬时"开始创建没加载/编辑器没就绪"
        safe_get(driver, CM_URL); time.sleep(2)
        if not click_contains(driver, "开始创建", 30):
            last = "没找到『开始创建 A+ 商品描述』"
            print(f"  (进编辑器重试 {attempt+1}: {last})"); continue
        time.sleep(3)
        click_contains(driver, "创建 高级", 20)  # 类型选择屏(若有)
        end = time.time() + 30
        while time.time() < end:
            if driver.find_elements(By.XPATH, '//*[contains(text(),"添加模块") or contains(text(),"Add Module")]'):
                return
            time.sleep(1)
        last = "编辑器未就绪(没出现『添加模块』)"
        print(f"  (进编辑器重试 {attempt+1}: {last})")
    raise RuntimeError(last)


def add_module(driver, module):
    """【已验证 6/6 的版本】精确文本(light DOM)+ 开库前后差集,点模块库新出现的磁贴。
    注:对标题非直接文本节点的模块(如双图)无效,那类单独处理。"""
    tile_xp = f'//*[normalize-space(text())="{module}"]'
    before = set(driver.find_elements(By.XPATH, tile_xp))
    for attempt in range(4):
        try:
            btns = [b for b in driver.find_elements(By.XPATH, '//*[normalize-space(text())="添加模块"]') if b.is_displayed()]
            (btns[-1] if btns else driver.find_element(By.XPATH, '//*[contains(text(),"添加模块")]')).click()
        except Exception:
            pass
        sent = False
        end = time.time() + 12
        while time.time() < end:
            box = driver.execute_script(JS_GALLERY_SEARCH)
            if box and not sent:
                try: box.clear(); box.send_keys(module); sent = True; time.sleep(2)
                except Exception: pass
            new = [e for e in driver.find_elements(By.XPATH, tile_xp) if e not in before and e.is_displayed()]
            if new:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});arguments[0].click();", new[-1])
                return True
            time.sleep(1)
        print(f"  (加模块重试 {attempt+1})")
    return False


JS_ADD_V2 = DEEP + """
var m=arguments[0].replace(/\\s/g,'');
var cands=deepAll(function(n){var t=(n.textContent||'').replace(/\\s/g,'');return t.indexOf(m)>=0;}).sort(function(a,b){return a.textContent.length-b.textContent.length;});
if(!cands.length) return 'no-tile';
var el=cands[0],p=el,best=el,d=0;
while(p&&d<7){var st=null;try{st=getComputedStyle(p);}catch(e){}
  if(p.tagName==='BUTTON'||p.tagName==='A'||(p.getAttribute&&p.getAttribute('role')==='button')||(st&&st.cursor==='pointer')){best=p;break;}
  p=p.parentElement;d++;}
try{best.scrollIntoView({block:'center'});}catch(e){}
var r=best.getBoundingClientRect();
var o={bubbles:true,cancelable:true,composed:true,clientX:r.left+r.width/2,clientY:r.top+r.height/2,view:window,button:0};
['pointerover','pointerenter','pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
  try{var E=(t.indexOf('pointer')===0)?PointerEvent:MouseEvent;best.dispatchEvent(new E(t,o));}catch(e){}
});
return 'clicked:'+best.tagName;
"""


def _editor_lang(driver):
    """判断编辑器 UI 语言:有 Add Module/Save as draft = 英文,否则简体。"""
    try:
        if driver.find_elements(By.XPATH, '//*[contains(text(),"Add Module") or contains(text(),"Save as draft")]'):
            return "en"
    except Exception:
        pass
    return "zh"


def add_module_v2(driver, module):
    """标题在子元素的模块(双图/四图等):shadow 搜索过滤 + selenium 原生点击磁贴(真实事件)。
    双语:先按本店 UI 语言只搜对应模块名(不来回跳);该语言搜不到任何磁贴才换另一种。"""
    lang = _editor_lang(driver)
    primary = TR.get(module, module) if lang == "en" else module
    secondary = module if lang == "en" else TR.get(module, module)
    name_order = [primary] + ([secondary] if secondary != primary else [])
    for name in name_order:
        tile_xp = f'//*[contains(normalize-space(.), "{name}")]'
        # 开库前的同名元素(含【已添加模块的标题】),用差集排除,只点库里"新出现"的磁贴
        before = set(driver.find_elements(By.XPATH, tile_xp))
        for attempt in range(3):
            try:
                btns = [b for b in driver.find_elements(By.XPATH, '//*[normalize-space(text())="添加模块" or normalize-space(text())="Add Module"]') if b.is_displayed()]
                (btns[-1] if btns else driver.find_element(By.XPATH, '//*[contains(text(),"添加模块") or contains(text(),"Add Module")]')).click()
            except Exception:
                pass
            e0 = time.time() + 8
            while time.time() < e0 and not driver.execute_script(JS_GALLERY_SEARCH):
                time.sleep(1)
            sbox = driver.execute_script(JS_GALLERY_SEARCH)
            if sbox:
                try:
                    sbox.click(); sbox.clear(); sbox.send_keys(name)
                except Exception:
                    driver.execute_script(
                        "var s=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(arguments[0]),'value').set;"
                        "s.call(arguments[0],arguments[1]);arguments[0].dispatchEvent(new Event('input',{bubbles:true}));",
                        sbox, name)
                time.sleep(2)
            # 只取【新出现】且可见的(排除已添加模块标题),按文本最短=最具体
            els = [e for e in driver.find_elements(By.XPATH, tile_xp) if e not in before and e.is_displayed()]
            els.sort(key=lambda e: len((e.text or "")))
            if not els:
                if sbox:                     # 库开了但没这名的磁贴 → 换另一种名(不来回跳)
                    print(f"  ({name} 搜不到磁贴,换名)")
                    break
                print(f"  (模块库未打开,重试 {attempt+1}: {name})")   # 库没开=瞬时 → 重试,不换名
                time.sleep(1.5)
                continue
            targets = els[:1]
            try: targets.append(els[0].find_element(By.XPATH, "./.."))
            except Exception: pass
            try: targets.append(els[0].find_element(By.XPATH, "./../.."))
            except Exception: pass
            for t in targets:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", t)
                    t.click()  # selenium 原生点击(真实事件序列)
                except Exception:
                    continue
                time.sleep(2)
                if not driver.execute_script(JS_GALLERY_SEARCH):  # 模块库已关 = 添加成功
                    print(f"  add_v2 成功(原生点击 / {name})")
                    return True
            print(f"  (加模块重试 {attempt+1}: {name})")
    return False


def add_image_module(driver, img, alt, idx, trigger_text="点击添加图片", ai_disclose=False, exclude_triggers=None, img_mobile=None):
    """假定模块已加;点图片触发器→ 传桌面图(+移动图)→ alt →(AI披露)→「添加」。
    img: 桌面图(1464×600);img_mobile: 移动图(600×450,可选,缺省复用桌面图);
    alt: 图片描述(SEO);exclude_triggers: 排除前面模块遗留的空图位,避免传错模块。"""
    exclude_triggers = exclude_triggers or set()
    # 打开图片对话框(重试):逐候选【原生点击】到拖拽区出现(有些触发器只认真实事件)
    opened = False
    for attempt in range(3):
        els = []
        for cand in both(trigger_text):       # 触发文案中英都试
            els = [e for e in driver.execute_script(JS_TRIGGERS, cand) if e not in exclude_triggers]
            if els:
                break
        print(f"    [{idx}] {trigger_text}候选={len(els)} try{attempt}")
        for cand in els[:4]:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cand)
                cand.click()  # 原生
            except Exception:
                try: driver.execute_script("arguments[0].click();", cand)
                except Exception: continue
            zt = time.time() + 8
            while time.time() < zt:
                if driver.execute_script(JS_ZONES):
                    opened = True; break
                time.sleep(1)
            if opened: break
        if opened: break
        time.sleep(2)
    if not opened:
        print(f"    [{idx}] 图片对话框未打开"); return False
    # 有几个空拖拽区就传几张(桌面/移动 1~2 个),每张重新注入 input
    def _close_dialog():
        click_label(driver, "取消", 5)  # 关掉图片对话框(Cancel),避免残留错误态卡死后续
    zone_imgs = [img, img_mobile or img]   # 第1格=桌面图,第2格=移动图(没给移动图就复用桌面图)
    uploaded = 0
    while uploaded < 2:
        zones = None
        e2 = time.time() + 18
        while time.time() < e2:
            zones = driver.execute_script(JS_ZONES)
            if zones: break
            time.sleep(1)
        if not zones:
            break  # 没有更多空拖拽区
        cur = zone_imgs[uploaded] if uploaded < len(zone_imgs) else img
        injf = driver.execute_script("var o=document.getElementById('__sel_up__');if(o)o.remove();" + JS_INJECT)
        injf.send_keys(cur); time.sleep(1)
        driver.execute_script(JS_DROP, zones[0])
        ue = time.time() + 60                        # 等上传(放长到 60s 容忍慢上传;清掉=完成)
        while time.time() < ue and _has(driver, "正在上传"):
            time.sleep(2)
        time.sleep(2)
        uploaded += 1
        print(f"    [{idx}] 已上传第{uploaded}张({'桌面' if uploaded == 1 else '移动'})")
    if uploaded == 0:
        print(f"    [{idx}] 无拖拽区"); _close_dialog(); return False

    # 填 alt:真实键盘输入(kat-input,JS写值不被校验),并校验非空后才确认
    def fill_alts():
        els = driver.execute_script(JS_GET_ALTS)
        for el in els:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                try: el.click()
                except Exception: pass
                el.send_keys(bmp(alt)[:100])      # Alt text 上限 100 字符,超长截断
                driver.execute_script("arguments[0].dispatchEvent(new Event('input',{bubbles:true}));arguments[0].dispatchEvent(new Event('change',{bubbles:true}));try{arguments[0].blur();}catch(e){}", el)
            except Exception as e:
                print(f"    [{idx}] alt输入异常 {e}")
        return len(els)

    print(f"    [{idx}] 首轮空alt={fill_alts()}")
    time.sleep(1)
    remaining = driver.execute_script(JS_GET_ALTS)
    if remaining:
        print(f"    [{idx}] 仍有空alt={len(remaining)},再补一次")
        fill_alts(); time.sleep(1)
        remaining = driver.execute_script(JS_GET_ALTS)
    if remaining:
        print(f"    [{idx}] alt 仍未填好({len(remaining)}),放弃本模块"); return False

    # AI 图片披露:勾选"由 AI/生成式 制作"复选框(仅当声明为 AI 生成)
    if ai_disclose:
        cb = driver.execute_script(JS_AI_DISCLOSE)
        if cb:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cb); cb.click()
            except Exception:
                try: driver.execute_script("arguments[0].click();", cb)
                except Exception: pass
            time.sleep(0.5)
            checked = driver.execute_script("var n=arguments[0];return !!(n.checked||(n.getAttribute&&n.getAttribute('checked')!==null&&n.getAttribute('checked')!=='false'));", cb)
            print(f"    [{idx}] AI披露勾选=True 选中态={checked}")
        else:
            print(f"    [{idx}] 未找到 AI披露勾选框(可能本图位不需要)")

    ok = click_label(driver, "添加")
    print(f"    [{idx}] 添加={ok}")
    e3 = time.time() + 30
    while time.time() < e3 and _has(driver, "拖到这里"):
        time.sleep(1)
    closed = not _has(driver, "拖到这里")
    if not closed:                       # Add 被拒(如缺图报错)→ 强制关闭对话框,避免卡死后续
        print(f"    [{idx}] 对话框未关(可能报错),强制 Cancel")
        _close_dialog(); time.sleep(2)
        return False
    print(f"    [{idx}] 对话框已关闭={closed}")
    return ok


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "/Users/zane/Desktop/dinosaur"
    label = os.path.basename(folder.rstrip("/"))
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else MAX_MODULES
    imgs = sorted(glob.glob(os.path.join(folder, "A+", "*.png")))[:limit]
    name = f"ZZTEST_{label}_" + time.strftime("%m%d_%H%M%S")
    print(f"文件夹={folder}  图数={len(imgs)}  草稿名={name}")

    with open(os.path.join(HERE, "config.yaml"), "r", encoding="utf-8") as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    z.download_driver(); z.kill_client(); z.start_client()
    if not z.wait_ready(max_wait=90):
        print("控制 API 未就绪"); return
    z.update_core()
    store = z.store_by_name(os.environ.get("ZINIAO_STORE", "XY"))
    print("目标店铺:", store.get("browserName"))
    oauth = store.get("browserOauth")
    driver = z.attach(z.open_store(oauth)); driver.implicitly_wait(8)
    out = os.path.join(HERE, "scratch"); os.makedirs(out, exist_ok=True)

    open_premium_editor(driver)
    print("编辑器已就绪(经 内容管理器→开始创建→创建高级A+ 进入)")

    for i, img in enumerate(imgs):
        if not add_module(driver, MODULE):
            print(f"  [{i}] 加模块失败"); continue
        ok = add_image_module(driver, img, f"{label} A+ {i+1}", i)
        print(f"  [{i}] {'OK' if ok else '失败'}  {os.path.basename(img)}")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    # 名称
    name_el = None
    e = time.time() + 15
    while time.time() < e and not name_el:
        name_el = driver.execute_script(JS_NAME_INPUT); time.sleep(1)
    if name_el:
        try: name_el.click()
        except Exception: pass
        name_el.send_keys(name)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input',{bubbles:true}));arguments[0].dispatchEvent(new Event('change',{bubbles:true}));try{arguments[0].blur();}catch(e){}", name_el)
        print("名称回读:", driver.execute_script("return arguments[0].value", name_el))

    print("点[保存为草稿]:", click_label(driver, "保存为草稿"))
    time.sleep(8)
    driver.save_screenshot(os.path.join(out, f"full_{label}.png"))
    print("落地 URL:", driver.current_url)
    txt = driver.execute_script("return document.body?document.body.innerText:''") or ""
    print("结果关键词:", [k for k in ["已保存", "验证失败", "错误", "失败", "必须填写", "草稿"] if k in txt])
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()

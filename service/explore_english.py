"""英文 UI 抓真实字符串:导航按钮、模块名(19个)、placeholder。用通用匹配逐步进入。"""
import json, os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import safe_get, CM_URL, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))

# 可见的"按钮类"文本(短)
JS_BUTTONS = DEEP + """
var out=[];
deepAll(function(n){
  var tag=n.tagName;
  if(!(tag==='BUTTON'||tag==='KAT-BUTTON'||tag==='A'||(n.getAttribute&&n.getAttribute('role')==='button'))) return false;
  var r=n.getBoundingClientRect&&n.getBoundingClientRect(); if(!(r&&r.width>0&&r.height>0)) return false;
  var t=(n.textContent||'').trim(); return t.length>0&&t.length<40;
}).forEach(function(n){var t=(n.textContent||'').trim(); if(out.indexOf(t)<0) out.push(t);});
return out;
"""
# 可见 placeholder
JS_PH = DEEP + "var o=[];deepAll(function(n){return (n.tagName==='INPUT'||n.tagName==='TEXTAREA');}).forEach(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();if(!(r&&r.width>0))return;var p=n.placeholder||'';var a=(n.getAttribute&&n.getAttribute('aria-label'))||'';if(p&&o.indexOf('ph:'+p)<0)o.push('ph:'+p);if(a&&o.indexOf('aria:'+a)<0)o.push('aria:'+a);});return o;"
# 通用点击:文本含子串(不分大小写),取最小可点元素
JS_CLICK_RE = DEEP + """
var sub=(''+arguments[0]).toLowerCase();
var cands=deepAll(function(n){var t=(n.textContent||'').trim();return t.toLowerCase().indexOf(sub)>=0 && t.length<60;});
cands=cands.filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>0&&r.height>0;});
cands.sort(function(a,b){return (a.textContent||'').length-(b.textContent||'').length;});
return cands.length?cands[0]:null;
"""


def click_re(driver, sub, wait=3):
    el = driver.execute_script(JS_CLICK_RE, sub)
    if not el:
        return False
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el); el.click()
    except Exception:
        try: driver.execute_script("arguments[0].click();", el)
        except Exception: return False
    time.sleep(wait); return True


def dump(driver, tag):
    print(f"\n--- {tag} ---")
    print("按钮:", json.dumps(driver.execute_script(JS_BUTTONS), ensure_ascii=False))
    print("placeholder:", json.dumps(driver.execute_script(JS_PH), ensure_ascii=False))


def main():
    with open(os.path.join(HERE, "config.yaml")) as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    z.download_driver(); z.kill_client(); z.start_client()
    if not z.wait_ready(90):
        print("控制API未就绪"); return
    z.update_core()
    store = z.store_by_name(os.environ.get("ZINIAO_STORE", "XY"))
    driver = z.attach(z.open_store(store.get("browserOauth"))); driver.implicitly_wait(8)

    safe_get(driver, CM_URL); time.sleep(5)
    dump(driver, "内容管理器首页(找 Start creating/Create)")
    driver.save_screenshot(os.path.join(HERE, "scratch", "en_1home.png"))

    click_re(driver, "creat", 4)  # Start creating A+ content
    dump(driver, "点 creat 后(可能出类型选择)")
    driver.save_screenshot(os.path.join(HERE, "scratch", "en_2create.png"))

    click_re(driver, "premium", 4)  # Create Premium A+
    time.sleep(3)
    dump(driver, "点 premium 后(编辑器,找 Add module / Content name)")
    driver.save_screenshot(os.path.join(HERE, "scratch", "en_3editor.png"))

    click_re(driver, "module", 4)  # Add module
    time.sleep(2)
    print("\n--- 模块库:全部模块名(英文,19个)---")
    print("按钮:", json.dumps(driver.execute_script(JS_BUTTONS), ensure_ascii=False))
    driver.save_screenshot(os.path.join(HERE, "scratch", "en_4gallery.png"))
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()

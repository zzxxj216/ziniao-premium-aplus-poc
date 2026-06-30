"""英文第二轮:用已知英文串正确进编辑器+开模块库,抓 模块名(19)/字段 placeholder/动作按钮。"""
import json, os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import safe_get, CM_URL, click_contains, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))

JS_PH = DEEP + "var o=[];deepAll(function(n){return (n.tagName==='INPUT'||n.tagName==='TEXTAREA');}).forEach(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();if(!(r&&r.width>0))return;var p=n.placeholder||'';var a=(n.getAttribute&&n.getAttribute('aria-label'))||'';if(p&&o.indexOf('ph:'+p)<0)o.push('ph:'+p);if(a&&o.indexOf('aria:'+a)<0)o.push('aria:'+a);});return o;"
# 可见叶子文本(模块名/标签):有文本、length 4..52
JS_LEAF = DEEP + """
var seen={},out=[];
deepAll(function(n){
  var r=n.getBoundingClientRect&&n.getBoundingClientRect(); if(!(r&&r.width>0&&r.height>0)) return false;
  var t=(n.textContent||'').trim(); if(t.length<3||t.length>52) return false;
  // 叶子:子元素没有同样的长文本
  for(var i=0;i<n.children.length;i++){ if((n.children[i].textContent||'').trim()===t) return false; }
  return true;
}).forEach(function(n){var t=(n.textContent||'').trim(); if(!seen[t]){seen[t]=1;out.push(t);}});
return out;
"""


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
    print("Start creating:", click_contains(driver, "Start creating A+ content", 30)); time.sleep(3)
    print("Create Premium:", click_contains(driver, "Create Premium A+", 25)); time.sleep(4)
    # 等编辑器
    end = time.time() + 30; ready = False
    while time.time() < end:
        if driver.find_elements(By.XPATH, '//*[contains(text(),"Add module")]'):
            ready = True; break
        time.sleep(1)
    print("编辑器就绪(Add module 出现):", ready)
    print("\n=== 编辑器 placeholder(找 Content name 等)===")
    print(json.dumps(driver.execute_script(JS_PH), ensure_ascii=False))
    print("\n=== 编辑器可见标签(找 Add module / Save 等)===")
    leaves = driver.execute_script(JS_LEAF)
    print(json.dumps([t for t in leaves if len(t) < 30], ensure_ascii=False))
    driver.save_screenshot(os.path.join(HERE, "scratch", "en2_editor.png"))

    # 开模块库
    print("\n点 Add module:", click_contains(driver, "Add module", 20)); time.sleep(3)
    print("=== 模块库:全部模块名(英文)===")
    print(json.dumps(driver.execute_script(JS_LEAF), ensure_ascii=False))
    print("模块库 placeholder:", json.dumps(driver.execute_script(JS_PH), ensure_ascii=False))
    driver.save_screenshot(os.path.join(HERE, "scratch", "en2_gallery.png"))
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()

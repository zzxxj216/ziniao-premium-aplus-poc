"""探查 AI 图片披露:传图后对话框里的披露勾选框(checkbox)文案/元素。"""
import json, os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import (open_premium_editor, add_module_v2, both, DEEP,
                        JS_TRIGGERS, JS_ZONES, JS_INJECT, JS_DROP, JS_HAS, _has)

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = "/Users/zane/Desktop/dinosaur/A+/ChatGPT Image 2026年6月23日 10_44_19 (1).png"

JS_CHECKBOXES = DEEP + """
var out=[];
deepAll(function(n){
  var tag=n.tagName||'';
  var isck=(tag==='INPUT'&&n.type==='checkbox')||tag==='KAT-CHECKBOX'||(n.getAttribute&&n.getAttribute('role')==='checkbox');
  if(!isck) return false;
  var r=n.getBoundingClientRect&&n.getBoundingClientRect(); return r&&r.width>0;
}).forEach(function(n){
  var lab=(n.getAttribute&&(n.getAttribute('label')||n.getAttribute('aria-label')))||'';
  var checked=n.checked||(n.getAttribute&&n.getAttribute('checked'))||'';
  out.push({tag:n.tagName, label:lab, checked:''+checked});
});
return out;
"""
JS_AI_LEAF = DEEP + """
var seen={},out=[];
deepAll(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();if(!(r&&r.width>0&&r.height>0))return false;
var t=(n.textContent||'').trim(); if(t.length<3||t.length>120)return false;
if(!/AI|disclos|generat|披露|生成|人工智能/i.test(t))return false;
for(var i=0;i<n.children.length;i++){if((n.children[i].textContent||'').trim()===t)return false;} return true;
}).forEach(function(n){var t=(n.textContent||'').trim();if(!seen[t]){seen[t]=1;out.push(t);}});return out;
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
    open_premium_editor(driver)
    print("加模块:", add_module_v2(driver, "带文本的单张高级图片")); time.sleep(3)
    # 打开图片对话框
    opened = False
    for cand in both("点击添加图片"):
        for el in driver.execute_script(JS_TRIGGERS, cand):
            try: driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el); el.click()
            except Exception: continue
            t = time.time() + 8
            while time.time() < t:
                if driver.execute_script(JS_ZONES): opened = True; break
                time.sleep(1)
            if opened: break
        if opened: break
    print("对话框打开:", opened)
    print("\n--- 传图前 checkboxes ---", json.dumps(driver.execute_script(JS_CHECKBOXES), ensure_ascii=False))
    # 传图
    zones = driver.execute_script(JS_ZONES)
    if zones:
        injf = driver.execute_script("var o=document.getElementById('__sel_up__');if(o)o.remove();" + JS_INJECT)
        injf.send_keys(IMG); time.sleep(1)
        driver.execute_script(JS_DROP, zones[0])
        ue = time.time() + 120
        while time.time() < ue and (_has(driver, "正在上传") or driver.execute_script(JS_HAS, "Uploading")):
            time.sleep(2)
        done = not (_has(driver, "正在上传") or driver.execute_script(JS_HAS, "Uploading"))
        print("上传完成:", done)
        time.sleep(6)  # 上传完成后再等披露框出现
    JS_ALL_LEAF = DEEP + """
    var seen={},out=[];
    deepAll(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();if(!(r&&r.width>0&&r.height>0))return false;
    var t=(n.textContent||'').trim(); if(t.length<3||t.length>90)return false;
    for(var i=0;i<n.children.length;i++){if((n.children[i].textContent||'').trim()===t)return false;} return true;
    }).forEach(function(n){var t=(n.textContent||'').trim();if(!seen[t]){seen[t]=1;out.push(t);}});return out;
    """
    print("\n--- 传图后 checkboxes ---", json.dumps(driver.execute_script(JS_CHECKBOXES), ensure_ascii=False))
    leaves = driver.execute_script(JS_ALL_LEAF)
    # 对话框区域文案(排除左侧导航)
    dialog = [t for t in leaves if t not in ("Products","Workspace","Orders","Finance","Marketing","Menu") and not t.startswith("Manage")]
    print("--- 传图后 对话框/页面叶子 ---", json.dumps(dialog, ensure_ascii=False))
    driver.save_screenshot(os.path.join(HERE, "scratch", "disclosure.png"))
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()

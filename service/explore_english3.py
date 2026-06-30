"""英文第三轮:开模块库抓19个模块名+搜索框;再加一个模块抓字段/图片/对话框英文串。"""
import json, os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import safe_get, CM_URL, click_contains, add_image_module, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
JS_PH = DEEP + "var o=[];deepAll(function(n){return (n.tagName==='INPUT'||n.tagName==='TEXTAREA');}).forEach(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();if(!(r&&r.width>0))return;var p=n.placeholder||'';if(p&&o.indexOf(p)<0)o.push(p);});return o;"
JS_LEAF = DEEP + """
var seen={},out=[];
deepAll(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();if(!(r&&r.width>0&&r.height>0))return false;
var t=(n.textContent||'').trim(); if(t.length<3||t.length>55)return false;
for(var i=0;i<n.children.length;i++){if((n.children[i].textContent||'').trim()===t)return false;} return true;
}).forEach(function(n){var t=(n.textContent||'').trim();if(!seen[t]){seen[t]=1;out.push(t);}});
return out;
"""
JS_CLICK_LEAF = DEEP + "var s=arguments[0];var a=deepAll(function(n){return (n.textContent||'').trim()===s;}).filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>0;});return a.length?a[0]:null;"


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
    click_contains(driver, "Start creating A+ content", 30); time.sleep(3)
    click_contains(driver, "Create Premium A+", 25); time.sleep(4)
    end = time.time() + 30
    while time.time() < end and not driver.find_elements(By.XPATH, '//*[contains(text(),"Add Module")]'):
        time.sleep(1)
    print("点 Add Module:", click_contains(driver, "Add Module", 20)); time.sleep(3)
    leaves = driver.execute_script(JS_LEAF)
    # 模块名:含 image/text/video/carousel/comparison/hotspot/background/specification/q&a 等关键词
    mods = [t for t in leaves if any(k in t.lower() for k in ["image","text","video","carousel","comparison","compar","hotspot","background","specification","q&a","question","four","single","standard"])]
    print("\n=== 模块库全部叶子 ===")
    print(json.dumps(leaves, ensure_ascii=False))
    print("\n=== 疑似模块名 ===")
    print(json.dumps(mods, ensure_ascii=False))
    print("模块库 placeholder:", json.dumps(driver.execute_script(JS_PH), ensure_ascii=False))
    driver.save_screenshot(os.path.join(HERE, "scratch", "en3_gallery.png"))

    # 加一个含图片的模块抓字段/图片串:优先点含 "image" 的最短叶子
    target = None
    for t in sorted(mods, key=len):
        if "image" in t.lower(): target = t; break
    print("\n选模块加:", target)
    if target:
        el = driver.execute_script(JS_CLICK_LEAF, target)
        if el:
            try: driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el); el.click()
            except Exception: driver.execute_script("arguments[0].click();", el)
            time.sleep(3)
            print("加完模块后 placeholder(字段名):", json.dumps(driver.execute_script(JS_PH), ensure_ascii=False))
            print("加完模块后叶子(找 Click to add image/Save 等):",
                  json.dumps([t for t in driver.execute_script(JS_LEAF) if len(t) < 32], ensure_ascii=False))
            driver.save_screenshot(os.path.join(HERE, "scratch", "en3_module.png"))
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()

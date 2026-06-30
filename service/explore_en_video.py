"""英文站抓视频触发真实串:加 Premium Full Video,dump 含 video 的叶子。"""
import json, os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
JS_LEAF = DEEP + """
var seen={},out=[];
deepAll(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();if(!(r&&r.width>0&&r.height>0))return false;
var t=(n.textContent||'').trim(); if(t.length<3||t.length>40)return false;
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
    print("加 Premium Full Video:", add_module_v2(driver, "高级全视频")); time.sleep(3)
    leaves = driver.execute_script(JS_LEAF)
    vid = [t for t in leaves if "video" in t.lower()]
    print("含 video 的叶子:", json.dumps(vid, ensure_ascii=False))
    print("\n完成。窗口保持打开。")

if __name__ == "__main__":
    main()

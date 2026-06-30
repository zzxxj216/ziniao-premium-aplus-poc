"""英文第四轮:加 Premium Single Image with Text,抓字段 placeholder + 图片对话框英文串。"""
import json, os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import safe_get, CM_URL, click_contains, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
JS_PH = DEEP + "var o=[];deepAll(function(n){return (n.tagName==='INPUT'||n.tagName==='TEXTAREA');}).forEach(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();if(!(r&&r.width>0))return;var p=n.placeholder||'';if(p&&o.indexOf(p)<0)o.push(p);});return o;"
JS_LEAF = DEEP + """
var seen={},out=[];
deepAll(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();if(!(r&&r.width>0&&r.height>0))return false;
var t=(n.textContent||'').trim(); if(t.length<3||t.length>40)return false;
for(var i=0;i<n.children.length;i++){if((n.children[i].textContent||'').trim()===t)return false;} return true;
}).forEach(function(n){var t=(n.textContent||'').trim();if(!seen[t]){seen[t]=1;out.push(t);}});return out;
"""
JS_CLICK_LEAF = DEEP + "var s=arguments[0];var a=deepAll(function(n){return (n.textContent||'').trim()===s;}).filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>0;});return a.length?a[a.length-1]:null;"
JS_CLICK_CONTAIN = DEEP + "var s=arguments[0].toLowerCase();var a=deepAll(function(n){return (n.textContent||'').trim().toLowerCase().indexOf(s)>=0&&(n.textContent||'').trim().length<30;}).filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>0;});a.sort(function(x,y){return x.textContent.length-y.textContent.length;});return a.length?a[0]:null;"


def native(driver, el):
    try: driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el); el.click(); return True
    except Exception:
        try: driver.execute_script("arguments[0].click();", el); return True
        except Exception: return False


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
    click_contains(driver, "Add Module", 20); time.sleep(2)
    # 搜索框输入 Single,缩小后点该模块
    el = driver.execute_script(JS_CLICK_LEAF, "Premium Single Image with Text")
    print("点模块:", native(driver, el) if el else "未找到"); time.sleep(3)

    print("\n=== 字段 placeholder(headline/subtitle/body)===")
    print(json.dumps(driver.execute_script(JS_PH), ensure_ascii=False))
    print("\n=== 模块内叶子(找 Click to add image)===")
    print(json.dumps(driver.execute_script(JS_LEAF), ensure_ascii=False))
    driver.save_screenshot(os.path.join(HERE, "scratch", "en4_module.png"))

    # 点图片触发,抓对话框串
    trig = driver.execute_script(JS_CLICK_CONTAIN, "add image") or driver.execute_script(JS_CLICK_CONTAIN, "image")
    print("\n点图片触发:", native(driver, trig) if trig else "未找到 image 触发"); time.sleep(3)
    print("=== 图片对话框 叶子(找 Drag/drop, Alternative text, Add)===")
    print(json.dumps(driver.execute_script(JS_LEAF), ensure_ascii=False))
    print("图片对话框 placeholder:", json.dumps(driver.execute_script(JS_PH), ensure_ascii=False))
    driver.save_screenshot(os.path.join(HERE, "scratch", "en4_imgdialog.png"))
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()

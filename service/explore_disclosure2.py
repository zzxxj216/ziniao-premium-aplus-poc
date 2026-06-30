"""诊断:Add Image 对话框有无隐藏 file input;若有,用 send_keys 真实上传,再看披露框/预览。"""
import json, os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, both, DEEP, JS_TRIGGERS, JS_ZONES, JS_HAS, _has

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = "/Users/zane/Desktop/dinosaur/A+/ChatGPT Image 2026年6月23日 10_44_19 (1).png"

JS_FILE_DEEP = DEEP + "var a=[];function w(r){try{r.querySelectorAll('input[type=file]').forEach(e=>a.push(e));r.querySelectorAll('*').forEach(e=>{if(e.shadowRoot)w(e.shadowRoot);if(e.tagName==='IFRAME'){try{if(e.contentDocument)w(e.contentDocument);}catch(x){}}});}catch(x){}}w(document);return a;"
JS_FULLTEXT = "return document.body?document.body.innerText:'';"
JS_AITEXT = DEEP + "var re=/generat|created using|ai-generated|ai generated|生成式|人工智能|disclos|披露|using ai|created with ai|AI tool/i;var out=[];deepAll(function(n){var t=(n.textContent||'').trim();if(t&&t.length<160&&re.test(t)){for(var i=0;i<n.children.length;i++){if((n.children[i].textContent||'').trim()===t)return false;}return true;}return false;}).forEach(function(n){out.push(n.tagName+':'+(n.textContent||'').trim().slice(0,120));});return out;"


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
    # 打开 Add Image 对话框
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
    files = driver.execute_script(JS_FILE_DEEP)
    print("对话框内 file input 数:", len(files))
    if files:
        fi = files[0]
        driver.execute_script("arguments[0].style.cssText='display:block!important;visibility:visible!important;opacity:1!important;width:10px;height:10px;position:fixed;left:0;top:0;z-index:99999';", fi)
        fi.send_keys(IMG)
        print("已 send_keys 真实上传,等完成...")
        ue = time.time() + 90
        while time.time() < ue and (_has(driver, "正在上传") or driver.execute_script(JS_HAS, "Uploading")):
            time.sleep(2)
        time.sleep(6)
        print("上传后 AI/披露文案:", json.dumps(driver.execute_script(JS_AITEXT), ensure_ascii=False))
    else:
        print("无 file input —— 仍需拖拽 hack")
    driver.save_screenshot(os.path.join(HERE, "scratch", "disclosure2.png"))
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()

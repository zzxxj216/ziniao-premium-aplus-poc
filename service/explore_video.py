"""探查视频上传:点「添加视频」后出现什么(视频库?上传对话框?file input?)。"""
import json, os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "高级全视频"

JS_FILE = DEEP + "var a=[];function w(r){try{r.querySelectorAll('input[type=file]').forEach(e=>a.push(e));r.querySelectorAll('*').forEach(e=>{if(e.shadowRoot)w(e.shadowRoot);if(e.tagName==='IFRAME'){try{if(e.contentDocument)w(e.contentDocument);}catch(x){}}});}catch(x){}}w(document);return a.length;"
JS_CANDS = DEEP + "return deepAll(function(n){var x=(n.textContent||'').trim();return x.indexOf('添加视频')>=0&&x.length<=10;}).filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>0;});"


def main():
    with open(os.path.join(HERE, "config.yaml")) as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    z.download_driver(); z.kill_client(); z.start_client()
    if not z.wait_ready(90):
        print("控制API未就绪"); return
    z.update_core()
    store = z.store_by_name(os.environ.get("ZINIAO_STORE", "XY"))
    driver = z.attach(z.open_store(store.get("browserOauth"))); driver.implicitly_wait(10)
    open_premium_editor(driver)
    print("加模块:", add_module_v2(driver, MODULE)); time.sleep(3)
    cands = driver.execute_script(JS_CANDS)
    print("『添加视频』候选:", len(cands))
    for i, e in enumerate(cands):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", e); e.click()
        except Exception as ex:
            print(f"  点[{i}]异常 {ex}"); continue
        time.sleep(4)
        body = driver.execute_script("return document.body?document.body.innerText:''") or ""
        kws = [k for k in ["拖到这里", "上传视频", "视频库", "选择视频", "URL", "正在处理", "替代文本", "浏览", "拖放", "添加视频文件"] if k in body]
        print(f"  点[{i}]后: file_input={driver.execute_script(JS_FILE)} 关键词={kws}")
        driver.save_screenshot(os.path.join(HERE, "scratch", f"video_click{i}.png"))
        if kws or driver.execute_script(JS_FILE):
            break
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()

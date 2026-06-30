"""高级全视频:加模块 → 填文 → 点「添加视频」露出 file input → send_keys 视频 → 等处理 →(添加)→ 存草稿。"""
import os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, click_label, DEEP
from build_generic import fill_text, fill_bodies, set_name

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "高级全视频"
VIDEO = "/Users/zane/Downloads/mothers_day/5cd32eaf-9009-4844-aec8-fe85132907d3.mp4"

JS_CANDS = DEEP + "return deepAll(function(n){var x=(n.textContent||'').trim();return x.indexOf('添加视频')>=0&&x.length<=10;}).filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>0;});"
JS_FILE_EL = DEEP + "var a=[];function w(r){try{r.querySelectorAll('input[type=file]').forEach(e=>a.push(e));r.querySelectorAll('*').forEach(e=>{if(e.shadowRoot)w(e.shadowRoot);if(e.tagName==='IFRAME'){try{if(e.contentDocument)w(e.contentDocument);}catch(x){}}});}catch(x){}}w(document);return a;"
JS_HAS = DEEP + "var s=arguments[0];return deepAll(function(n){return (n.textContent||'').includes(s);}).length>0;"


def main():
    print("视频存在:", os.path.exists(VIDEO))
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
    print("加模块(v2):", add_module_v2(driver, MODULE)); time.sleep(3)
    print("填文本框:", fill_text(driver)); print("填正文:", fill_bodies(driver))
    name = "ZZTEST_video_" + time.strftime("%H%M%S")
    print("命名(提前):", set_name(driver, name))   # 视频上传前先设名,避免上传后名称框被遮挡

    # 点添加视频露出 file input
    fi = None
    for c in driver.execute_script(JS_CANDS):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", c); c.click()
        except Exception:
            continue
        time.sleep(3)
        if driver.execute_script(JS_FILE_EL):
            break

    def grab_and_send():
        # 顶层
        driver.switch_to.default_content()
        ins = driver.find_elements(By.CSS_SELECTOR, "input[type=file]")
        if ins:
            driver.execute_script("arguments[0].style.cssText='display:block!important;visibility:visible!important;opacity:1!important;width:10px;height:10px;position:fixed;left:0;top:0;z-index:99999';", ins[0])
            ins[0].send_keys(VIDEO); return "top"
        # 各 iframe
        for fr in driver.find_elements(By.TAG_NAME, "iframe"):
            driver.switch_to.default_content()
            try:
                driver.switch_to.frame(fr)
                ins = driver.find_elements(By.CSS_SELECTOR, "input[type=file]")
                if ins:
                    driver.execute_script("arguments[0].style.cssText='display:block!important;visibility:visible!important;opacity:1!important;width:10px;height:10px;position:fixed;left:0;top:0;z-index:99999';", ins[0])
                    ins[0].send_keys(VIDEO)
                    return "iframe"
            except Exception:
                continue
        driver.switch_to.default_content()
        return None

    where = grab_and_send()
    driver.switch_to.default_content()
    if not where:
        print("没找到可交互的视频 file input(可能在 shadow)"); return
    print(f"视频已 send_keys(在 {where}),等上传/处理...")
    # 等"正在上传/处理"结束(最多 180s)
    end = time.time() + 180
    while time.time() < end:
        if not (driver.execute_script(JS_HAS, "正在上传") or driver.execute_script(JS_HAS, "正在处理") or driver.execute_script(JS_HAS, "上传中")):
            break
        time.sleep(5)
    print("上传/处理阶段结束(或超时)")
    driver.save_screenshot(os.path.join(HERE, "scratch", "video_uploaded.png"))
    # 可能有 添加/确认
    for lbl in ["添加", "确认", "保存"]:
        if driver.execute_script(JS_HAS, "替代文本") or driver.execute_script(JS_HAS, "拖到这里"):
            break
    click_label(driver, "添加"); time.sleep(3)

    print("保存草稿:", click_label(driver, "保存为草稿"))
    time.sleep(8)
    driver.save_screenshot(os.path.join(HERE, "scratch", "video_done.png"))
    txt = driver.execute_script("return document.body?document.body.innerText:''") or ""
    print("URL:", driver.current_url)
    print("结果:", [k for k in ["已保存", "验证失败", "必须填写", "错误", "草稿", "处理"] if k in txt])
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()

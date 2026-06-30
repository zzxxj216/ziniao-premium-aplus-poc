"""
跑通"带文本的单张高级图片"(图文类第一个):加模块 → 真实键入 标题/副标题/正文 →
上传图片(复用) → 命名 → 保存草稿。占位文案。
"""
import os
import time

import yaml

from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module, add_image_module, click_label, DEEP, JS_NAME_INPUT

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = "/Users/zane/Desktop/dinosaur/A+/ChatGPT Image 2026年6月23日 10_44_19 (1).png"
MODULE = "带文本的单张高级图片"
NAME = "ZZTEST_singletext_" + time.strftime("%m%d_%H%M%S")
TEXTS = {
    "输入标题文本": "Waterproof & Durable Dinosaur Name Labels",
    "输入子标题文本": "Great for School, Daycare & Camp",
    "输入正文文本": "Personalized dinosaur name labels in 10 cute designs. Dishwasher & microwave safe, fade-resistant, and easy to apply.",
}

JS_BY_PH = DEEP + "var ph=arguments[0];return deepAll(n=>(n.tagName==='INPUT'||n.tagName==='TEXTAREA')&&((n.placeholder||'')===ph||(n.getAttribute&&n.getAttribute('aria-label')===ph)));"
# 正文是 Draft.js 富文本:div.public-DraftEditor-content[role=textbox]
JS_BODY = DEEP + "return deepAll(n=>n.tagName==='DIV'&&n.isContentEditable&&(''+(n.className||'')).includes('public-DraftEditor-content'));"


def fill_ph(driver, ph, text):
    # 正文走 Draft.js
    if ph == "输入正文文本":
        els = [e for e in driver.execute_script(JS_BODY) if e.is_displayed() and not (e.text or "").strip()]
        if not els:
            return False
        el = els[0]
        try: el.click()
        except Exception: pass
        el.send_keys(text)
        return True
    els = [e for e in driver.execute_script(JS_BY_PH, ph) if e.is_displayed()]
    if not els:
        return False
    el = els[-1]
    try: el.click()
    except Exception: pass
    el.send_keys(text)
    driver.execute_script("arguments[0].dispatchEvent(new Event('input',{bubbles:true}));arguments[0].dispatchEvent(new Event('change',{bubbles:true}));try{arguments[0].blur();}catch(e){}", el)
    return True


def set_name(driver, name):
    el = None
    e = time.time() + 15
    while time.time() < e and not el:
        el = driver.execute_script(JS_NAME_INPUT); time.sleep(1)
    if not el:
        return False
    try: el.click()
    except Exception: pass
    el.send_keys(name)
    driver.execute_script("arguments[0].dispatchEvent(new Event('input',{bubbles:true}));arguments[0].dispatchEvent(new Event('change',{bubbles:true}));try{arguments[0].blur();}catch(e){}", el)
    return (driver.execute_script("return arguments[0].value", el) or "").strip() != ""


def main():
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
    driver = z.attach(z.open_store(oauth)); driver.implicitly_wait(10)
    out = os.path.join(HERE, "scratch"); os.makedirs(out, exist_ok=True)

    open_premium_editor(driver)
    print("加模块:", add_module(driver, MODULE)); time.sleep(3)

    for ph, txt in TEXTS.items():
        print(f"  填[{ph}]:", fill_ph(driver, ph, txt)); time.sleep(0.5)

    print("上传图片:", add_image_module(driver, IMG, "dinosaur single image", 0))
    print("命名:", set_name(driver, NAME))
    print("保存草稿:", click_label(driver, "保存为草稿"))
    time.sleep(8)
    driver.save_screenshot(os.path.join(out, "text_module_saved.png"))
    print("URL:", driver.current_url)
    txt = driver.execute_script("return document.body?document.body.innerText:''") or ""
    print("结果:", [k for k in ["已保存", "验证失败", "必须填写", "错误", "草稿"] if k in txt])
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()

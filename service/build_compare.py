"""高级比较表2:填 模块标题 + ASIN(真实)+ 图片标题 + 功能标签 + 产品图 → 存草稿。"""
import os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, add_image_module, click_label, DEEP
from build_generic import set_name

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "高级比较表2"
ASINS = ["B0D81DLXSJ", "B0H28WPJ33"]
IMG = "/Users/zane/Desktop/dinosaur/A+/ChatGPT Image 2026年6月23日 10_44_19 (1).png"

JS_BY_PH = DEEP + "var ph=arguments[0];return deepAll(function(n){return (n.tagName==='INPUT'||n.tagName==='TEXTAREA')&&(n.placeholder||'')===ph;}).filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>0;});"


def fill_ph(driver, ph, values):
    els = driver.execute_script(JS_BY_PH, ph)
    n = 0
    for el, v in zip(els, values):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.click(); el.send_keys(v); n += 1
        except Exception:
            pass
    return f"{n}/{len(els)}"


def fill_ph_all(driver, ph, value):
    els = driver.execute_script(JS_BY_PH, ph)
    n = 0
    for el in els:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.click(); el.send_keys(value); n += 1
        except Exception:
            pass
    return n


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
    print("加模块(v2):", add_module_v2(driver, MODULE)); time.sleep(3)
    print("命名(提前):", set_name(driver, "ZZTEST_compare_" + time.strftime("%H%M%S")))

    print("填 ASIN:", fill_ph(driver, "输入ASIN", ASINS))
    print("填图片标题:", fill_ph_all(driver, "输入图片标题文本", "Dino Labels"))
    print("填标题/功能:", fill_ph_all(driver, "输入标题文本", "Feature"))
    # 传产品图(前几个点击添加图片)
    up = 0
    for k in range(len(ASINS)):
        slots = [e for e in driver.find_elements(By.XPATH, '//*[contains(text(),"点击添加图片")]') if e.is_displayed()]
        if not slots: break
        if add_image_module(driver, IMG, f"product{k+1}", k): up += 1
    print("传产品图:", up)

    print("保存草稿:", click_label(driver, "保存为草稿"))
    time.sleep(8)
    driver.save_screenshot(os.path.join(HERE, "scratch", "compare2_done.png"))
    txt = driver.execute_script("return document.body?document.body.innerText:''") or ""
    print("URL:", driver.current_url)
    print("结果:", [k for k in ["已保存", "验证失败", "必须填写", "错误", "无效", "ASIN", "草稿"] if k in txt])
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()

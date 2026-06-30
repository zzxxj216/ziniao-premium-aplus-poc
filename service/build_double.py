"""跑通"包含文本的高级双图片":v2加模块 → 左右各上传1图 → 各填标题+正文 → 命名 → 存草稿。占位文案。"""
import glob, os, time
import yaml
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, add_image_module, click_label, DEEP, JS_NAME_INPUT

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "包含文本的高级双图片"
FOLDER = "/Users/zane/Desktop/dinosaur"
NAME = "ZZTEST_double_" + time.strftime("%m%d_%H%M%S")
TITLES = ["Durable & Waterproof", "10 Cute Designs"]
BODIES = ["Personalized dinosaur name labels, dishwasher safe.",
          "Great for school, daycare and camp. Easy to apply."]

JS_TITLES = DEEP + "return deepAll(n=>n.tagName==='INPUT'&&(n.placeholder||'')==='输入标题文本');"
JS_BODIES = DEEP + "return deepAll(n=>n.tagName==='DIV'&&n.isContentEditable&&(''+(n.className||'')).includes('public-DraftEditor-content'));"


def fill_each(driver, getter_js, texts, is_body=False):
    els = [e for e in driver.execute_script(getter_js) if e.is_displayed()]
    if is_body:
        els = [e for e in els if not (e.text or "").strip()]
    n = 0
    for el, txt in zip(els, texts):
        try:
            el.click(); el.send_keys(txt); n += 1
        except Exception as e:
            print("   填字段异常:", e)
    return f"{n}/{len(els)}"


def set_name(driver, name):
    el = None; e = time.time() + 15
    while time.time() < e and not el:
        el = driver.execute_script(JS_NAME_INPUT); time.sleep(1)
    if not el: return False
    try: el.click()
    except Exception: pass
    el.send_keys(name)
    driver.execute_script("arguments[0].dispatchEvent(new Event('input',{bubbles:true}));arguments[0].dispatchEvent(new Event('change',{bubbles:true}));try{arguments[0].blur();}catch(e){}", el)
    return (driver.execute_script("return arguments[0].value", el) or "").strip() != ""


def main():
    imgs = sorted(glob.glob(os.path.join(FOLDER, "A+", "*.png")))[:2]
    with open(os.path.join(HERE, "config.yaml")) as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    z.download_driver(); z.kill_client(); z.start_client()
    if not z.wait_ready(90):
        print("控制API未就绪"); return
    z.update_core()
    store = z.store_by_name(os.environ.get("ZINIAO_STORE", "XY"))
    print("目标店铺:", store.get("browserName"))
    driver = z.attach(z.open_store(store.get("browserOauth"))); driver.implicitly_wait(8)

    open_premium_editor(driver)
    print("加模块(v2):", add_module_v2(driver, MODULE)); time.sleep(3)

    # 左右两个图位:连续上传 2 张(每次填 add_image_module 里最后一个空图位)
    for i, img in enumerate(imgs):
        print(f"上传图{i}:", add_image_module(driver, img, f"double img {i+1}", i))

    print("填标题:", fill_each(driver, JS_TITLES, TITLES))
    print("填正文:", fill_each(driver, JS_BODIES, BODIES, is_body=True))

    print("命名:", set_name(driver, NAME))
    print("保存草稿:", click_label(driver, "保存为草稿"))
    time.sleep(8)
    driver.save_screenshot(os.path.join(HERE, "scratch", "double_done.png"))
    print("URL:", driver.current_url)
    txt = driver.execute_script("return document.body?document.body.innerText:''") or ""
    print("结果:", [k for k in ["已保存", "验证失败", "必须填写", "错误", "草稿"] if k in txt])
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()

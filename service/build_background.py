"""包含文本的高级背景图片:加模块 → 填文 → 用「添加背景图片」触发上传背景图 → 命名 → 存草稿。"""
import os, time
import yaml
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, add_image_module, click_label
from build_generic import fill_text, fill_bodies, set_name

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "包含文本的高级背景图片"
IMG = "/Users/zane/Desktop/dinosaur/A+/ChatGPT Image 2026年6月23日 10_44_19 (1).png"


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
    print("填文本框:", fill_text(driver))
    print("填正文:", fill_bodies(driver))
    print("传背景图:", add_image_module(driver, IMG, "dinosaur background", 0, trigger_text="添加背景图片"))
    name = "ZZTEST_bg_" + time.strftime("%H%M%S")
    print("命名:", set_name(driver, name))
    print("保存草稿:", click_label(driver, "保存为草稿"))
    time.sleep(8)
    driver.save_screenshot(os.path.join(HERE, "scratch", "bg_done.png"))
    txt = driver.execute_script("return document.body?document.body.innerText:''") or ""
    print("URL:", driver.current_url)
    print("结果:", [k for k in ["已保存", "验证失败", "必须填写", "错误", "草稿"] if k in txt])
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()

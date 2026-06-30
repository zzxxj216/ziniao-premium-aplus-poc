"""轮播 handler:逐面板(点 面板(N/..) 标签 → 传图 → 填该面板文本)。
用法: python build_carousel.py "高级、简单的图像轮播" [面板数]"""
import glob, os, sys, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, add_image_module, click_label, JS_IMG_SLOTS
from build_generic import fill_text, fill_bodies, set_name

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = "/Users/zane/Desktop/dinosaur"


def click_panel(driver, n, exclude=None):
    """点面板(N)标签——逐个候选元素点,直到图位出现(标签有多个重复元素)。
    双语:简体「面板(N/..)」/ 英文「PANEL (N / ..)」。
    exclude: 排除前一个轮播的面板标签(多轮播时同号面板会串,必须只点当前轮播的)。"""
    exclude = exclude or set()
    xp = (f'//*[starts-with(normalize-space(.),"面板({n}/") '
          f'or starts-with(normalize-space(.),"PANEL ({n} /")]')
    tabs = [e for e in driver.find_elements(By.XPATH, xp) if e.is_displayed() and e not in exclude]
    for e in tabs:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", e)
            e.click()  # selenium 原生
            time.sleep(1.5)
            if driver.execute_script(JS_IMG_SLOTS):
                return True
        except Exception:
            continue
    return bool(tabs)


def main():
    module = sys.argv[1] if len(sys.argv) > 1 else "高级、简单的图像轮播"
    npan = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    imgs = sorted(glob.glob(os.path.join(FOLDER, "A+", "*.png")))
    name = "ZZTEST_" + "".join(c for c in module if c.isalnum())[:6] + "_" + time.strftime("%H%M%S")
    print(f"模块={module} 面板数={npan} 草稿名={name}")

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
    print("加模块(v2):", add_module_v2(driver, module)); time.sleep(3)

    for n in range(1, npan + 1):
        sw = click_panel(driver, n)
        # 切面板后等该面板图位渲染出来再传(穿透 shadow 检测)
        end = time.time() + 15
        while time.time() < end and not driver.execute_script(JS_IMG_SLOTS):
            time.sleep(1)
        print(f"面板{n} 切换={sw} 图位={len(driver.execute_script(JS_IMG_SLOTS))}")
        ok = add_image_module(driver, imgs[(n - 1) % len(imgs)], f"panel {n}", n)
        print(f"  面板{n} 传图={ok}")
        ft = fill_text(driver); fb = fill_bodies(driver)
        print(f"  面板{n} 文本={ft} 正文={fb}")

    print("命名:", set_name(driver, name))
    print("保存草稿:", click_label(driver, "保存为草稿"))
    time.sleep(8)
    driver.save_screenshot(os.path.join(HERE, "scratch", "carousel_done.png"))
    print("URL:", driver.current_url)
    txt = driver.execute_script("return document.body?document.body.innerText:''") or ""
    print("结果:", [k for k in ["已保存", "验证失败", "必须填写", "错误", "草稿"] if k in txt])
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()

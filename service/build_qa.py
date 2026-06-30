"""高级问答 5 组:加模块 → 点「添加问题」加到 5 组 → 填 10 个框 → 命名 → 存草稿。"""
import os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, click_label, click_contains, DEEP
from build_generic import fill_text, set_name

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "高级问答"
TARGET = 5

JS_TEXT_COUNT = DEEP + "return deepAll(function(n){return (n.tagName==='INPUT'||n.tagName==='TEXTAREA')&&(n.placeholder||(n.getAttribute&&n.getAttribute('aria-label')))&&!/搜索|替代文本|反馈|商品描述名称/.test((n.placeholder||'')+((n.getAttribute&&n.getAttribute('aria-label'))||''));}).filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>5;}).length;"


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
    print("初始文本框数:", driver.execute_script(JS_TEXT_COUNT))

    # 点「添加问题」加行,直到字段数不再增长或达到 5 组(10 框)
    for i in range(TARGET):
        before = driver.execute_script(JS_TEXT_COUNT)
        if before >= TARGET * 2:
            break
        ok = click_contains(driver, "添加问题", 8)
        time.sleep(1.5)
        after = driver.execute_script(JS_TEXT_COUNT)
        print(f"  点添加问题#{i+1}: {ok}  文本框 {before}->{after}")
        if after <= before:
            break

    name = "ZZTEST_qa5_" + time.strftime("%H%M%S")
    print("填文本框:", fill_text(driver))
    print("命名:", set_name(driver, name))
    print("保存草稿:", click_label(driver, "保存为草稿"))
    time.sleep(8)
    driver.save_screenshot(os.path.join(HERE, "scratch", "qa5.png"))
    txt = driver.execute_script("return document.body?document.body.innerText:''") or ""
    print("URL:", driver.current_url)
    print("结果:", [k for k in ["已保存", "验证失败", "必须填写", "错误", "草稿"] if k in txt])
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()

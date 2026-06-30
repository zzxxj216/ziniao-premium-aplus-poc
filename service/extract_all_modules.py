"""
逐个添加全部 19 个高级 A+ 模块,提取每个模块的字段/规格(去掉页面外壳的 innerText)
+ 截图。一次浏览器会话内完成;每个模块用深链开新空白编辑器,绝不保存(不产生草稿)。

产出:
  scratch/module_specs.txt   每个模块的字段清单
  scratch/mod_NN_*.png       每个模块添加后的截图
"""
import os
import re
import time

import yaml
from selenium.webdriver.common.by import By

from ziniao_client import ZiniaoClient

HERE = os.path.dirname(os.path.abspath(__file__))
EDITOR_URL = "https://sellercentral.amazon.com/enhanced-content/content-manager/workflow/ebc-premium/content/new/edit"

MODULES = [
    "优质视频图像轮播", "包含文本的高级双图片", "包含文本的高级背景图片", "包含文本的高级视频",
    "带文本的单张高级图片", "高级、简单的图像轮播", "高级全视频", "高级四图片和文本",
    "高级完整图片", "高级导航轮播", "高级技术规格", "高级文本",
    "高级比较表1", "高级比较表2", "高级比较表3", "高级热点1", "高级热点2",
    "高级规则轮播", "高级问答",
]

# 页面外壳 + 模块库名 + 语言项,提取时排除,只留模块自身字段
CHROME = set(MODULES) | {
    "Okalinq", "美国", "新版卖家平台", "ZH", "帮助", "取消", "保存为草稿", "下一步： 应用 ASIN",
    "最佳实践", "创建内容", "应用亚马逊商品编码(ASIN)", "提交", "批准", "已发布",
    "* 商品描述名称商品描述名称", "* 语言语言", "商品描述类型商品描述类型", "EBC",
    "状态状态", "草稿", "已使用的 ASIN已使用的 ASIN", "0", "编辑", "预览", "添加模块",
    "反馈", "帮助 计划政策", "下载“亚马逊卖家”移动应用",
    "English", "中文(简体)", "Deutsch", "Español", "Français", "Italiano",
    "日本語", "한국어", "ไทย", "Tiếng Việt", "हिंदी", "தமிழ்", "Português", "中文(繁體)",
    "上次活动上次活动",
}


def sanitize(s):
    return re.sub(r"[^0-9A-Za-z一-鿿]+", "_", s)[:24]


def main():
    with open(os.path.join(HERE, "config.yaml"), "r", encoding="utf-8") as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    z.download_driver()
    z.kill_client(); z.start_client()
    if not z.wait_ready(max_wait=90):
        print("控制 API 未就绪"); return
    z.update_core()
    oauth = z.amazon_stores(site_id="1")[0].get("browserOauth")
    driver = z.attach(z.open_store(oauth))
    driver.implicitly_wait(12)
    out_dir = os.path.join(HERE, "scratch"); os.makedirs(out_dir, exist_ok=True)
    report = open(os.path.join(out_dir, "module_specs.txt"), "w", encoding="utf-8")

    def log(s=""):
        print(s); report.write(s + "\n"); report.flush()

    for i, mod in enumerate(MODULES):
        log(f"\n########## [{i:02d}] {mod} ##########")
        try:
            driver.get(EDITOR_URL); time.sleep(6)
            if "/ap/" in driver.current_url:
                log("  被弹登录,终止"); break
            # 打开模块库
            driver.find_element(By.XPATH, '//*[contains(text(),"添加模块")]').click()
            time.sleep(3)
            # 模块库内搜索(用非全局的搜索框)
            try:
                boxes = [b for b in driver.find_elements(By.XPATH, '//input[@placeholder="搜索"]')
                         if b.get_attribute("id") != "sc-search-field" and b.is_displayed()]
                if boxes:
                    boxes[-1].clear(); boxes[-1].send_keys(mod); time.sleep(2)
            except Exception as e:
                log(f"  (搜索框异常: {e})")
            # 点该模块磁贴
            tile = driver.find_element(By.XPATH, f'//*[normalize-space(text())="{mod}"]')
            driver.execute_script("arguments[0].click();", tile)
            time.sleep(4)
            # 可能需要确认"添加"按钮
            for t in ["添加此模块", "添加模块", "添加"]:
                try:
                    btns = [b for b in driver.find_elements(By.XPATH, f'//button[normalize-space(.)="{t}"]') if b.is_displayed()]
                    if btns:
                        driver.execute_script("arguments[0].click();", btns[-1]); time.sleep(3); break
                except Exception:
                    pass
            driver.save_screenshot(os.path.join(out_dir, f"mod_{i:02d}_{sanitize(mod)}.png"))
            txt = driver.execute_script("return document.body ? document.body.innerText : ''") or ""
            lines = [l.strip() for l in txt.splitlines() if l.strip()]
            fields = list(dict.fromkeys([l for l in lines if l not in CHROME and l != mod]))
            log(f"  字段/规格 ({len(fields)} 项):")
            for l in fields[:60]:
                log(f"    · {l}")
        except Exception as e:
            log(f"  !! 处理失败: {e}")

    report.close()
    print("\n全部完成。窗口保持打开。未保存任何草稿。")


if __name__ == "__main__":
    main()

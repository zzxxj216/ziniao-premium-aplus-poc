"""调研 19 个模块的图片/视频尺寸要求:逐个模块打开编辑器,读图位标注的尺寸(只读不保存)。"""
import json, os, time
import yaml
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))

# 19 个模块(后台真实名)
MODULES = [
    "高级完整图片", "带文本的单张高级图片", "包含文本的高级双图片", "高级四图片和文本",
    "高级文本", "包含文本的高级背景图片", "高级问答", "高级技术规格",
    "高级、简单的图像轮播", "高级规则轮播", "高级导航轮播", "优质视频图像轮播",
    "高级全视频", "包含文本的高级视频",
    "高级比较表1", "高级比较表2", "高级比较表3", "高级热点1", "高级热点2",
]

# 抓"尺寸/比例/px/min/视频"相关的可见叶子文本
JS_DIMS = DEEP + r"""
var seen={},out=[];
var re=/(\d{2,4}\s*[:×x]\s*\d{2,4})|(\d{2,4}\s*px)|min\]|aspect|ratio|视频|video|\.mp4/i;
deepAll(function(n){
  var r=n.getBoundingClientRect&&n.getBoundingClientRect(); if(!(r&&r.width>0&&r.height>0))return false;
  var t=(n.textContent||'').trim(); if(t.length<2||t.length>70)return false;
  if(!re.test(t))return false;
  for(var i=0;i<n.children.length;i++){if((n.children[i].textContent||'').trim()===t)return false;}
  return true;
}).forEach(function(n){var t=(n.textContent||'').trim();if(!seen[t]){seen[t]=1;out.push(t);}});
return out;
"""


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

    results = {}
    for mod in MODULES:
        try:
            open_premium_editor(driver)               # 每个模块一个干净编辑器(不保存→不建草稿)
            ok = add_module_v2(driver, mod); time.sleep(3)
            dims = driver.execute_script(JS_DIMS) if ok else ["<加模块失败>"]
            results[mod] = dims
            print(f"### {mod}: {json.dumps(dims, ensure_ascii=False)}")
        except Exception as e:
            results[mod] = [f"<异常 {e}>"]
            print(f"### {mod}: 异常 {e}")
    open(os.path.join(HERE, "scratch", "image_reqs.json"), "w").write(json.dumps(results, ensure_ascii=False, indent=2))
    print("\nDONE")


if __name__ == "__main__":
    main()

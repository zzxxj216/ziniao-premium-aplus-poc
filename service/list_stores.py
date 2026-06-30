"""列出紫鸟所有店铺(名称/站点/oauth),用于按名选店。"""
import os
import yaml
from ziniao_client import ZiniaoClient

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    with open(os.path.join(HERE, "config.yaml")) as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    z.download_driver(); z.kill_client(); z.start_client()
    if not z.wait_ready(90):
        print("控制API未就绪"); return
    z.update_core()
    for b in z.list_browsers():
        print(f"  name={b.get('browserName')!r}  siteId={b.get('siteId')}  "
              f"platform={b.get('platform') or b.get('platformName')}  oauth={b.get('browserOauth')}")
    z.exit_client()
    print("完成。")


if __name__ == "__main__":
    main()

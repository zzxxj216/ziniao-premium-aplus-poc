"""
中心服务:把 create_aplus 暴露成 HTTP API,供运营侧 Claude Code(瘦技能)调用。
部署在那台装了紫鸟的公共电脑上。

依赖: pip install fastapi uvicorn
启动: APLUS_API_KEY=xxx  ZINIAO_COMPANY=..  ZINIAO_USERNAME=..  ZINIAO_PASSWORD=..  \
      uvicorn server:app --host 0.0.0.0 --port 8848

鉴权: 请求头 X-API-Key 必须等于环境变量 APLUS_API_KEY。
注意: 浏览器自动化是串行的,一次只处理一个创建请求(简单起见同步执行)。
"""
import os
import threading
import time
import traceback
from multiprocessing import get_context
from pathlib import Path
from queue import Empty

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from pydantic import BaseModel

from aplus_api import create_aplus
from ziniao_client import ZiniaoClient

# 运营端图片传到这里(服务端本地),再在 spec 里用返回的服务端路径
UPLOAD_DIR = os.environ.get("APLUS_UPLOAD_DIR") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "uploads")


def _load_local_env():
    """Load private machine env files without overwriting already exported vars."""
    paths = [
        Path(__file__).resolve().parent / ".env",
        Path.home() / ".codex" / "skills" / "ziniao-premium-aplus" / ".env",
        Path.home() / ".claude" / "skills" / "ziniao-premium-aplus" / ".env",
    ]
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text(errors="ignore").splitlines():
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            if raw.startswith("export "):
                raw = raw[len("export "):].strip()
            key, value = raw.split("=", 1)
            key = key.strip()
            if not key or key in os.environ:
                continue
            value = value.strip().strip("\"'")
            os.environ[key] = value


_load_local_env()

app = FastAPI(title="Ziniao Premium A+ Service")
_ctx = get_context("spawn")
_current_process = None
_current_task = {"name": None, "started_at": None}
_state_lock = threading.Lock()
REQUEST_TIMEOUT_SECONDS = int(os.environ.get("APLUS_REQUEST_TIMEOUT_SECONDS", "1200"))

SUPPORTED = ["完整图片", "单图文", "双图", "四图", "文本", "背景图片", "问答", "技术规格",
             "轮播", "视频", "含文本视频", "对比表1", "对比表2", "对比表3", "热点1", "热点2"]


class Spec(BaseModel):
    store: str | None = None       # 紫鸟店铺名,默认取服务端 ZINIAO_STORE
    name: str                      # 内容描述名称(必填)
    modules: list[dict]            # 透传每个模块的全部字段(images/texts/video/asins/hotspots/variant/title…),不丢字段


def _check(key):
    expected = os.environ.get("APLUS_API_KEY")
    if not expected or key != expected:
        raise HTTPException(status_code=401, detail="无效的 X-API-Key")


@app.get("/health")
def health():
    return {"ok": True, "supported_modules": SUPPORTED}


@app.post("/aplus/upload")
async def upload(files: list[UploadFile] = File(...), x_api_key: str = Header(default="")):
    """运营端把本机图片传到服务端;返回服务端绝对路径(在 spec 里用这些路径)。
    用法: curl -F files=@a.png -F files=@b.png $BASE/aplus/upload -H 'X-API-Key: ...'
    """
    _check(x_api_key)
    import shutil, uuid
    sess = uuid.uuid4().hex[:12]
    dest_dir = os.path.join(UPLOAD_DIR, sess)
    os.makedirs(dest_dir, exist_ok=True)
    paths = {}
    for f in files:
        name = os.path.basename(f.filename or "file")
        p = os.path.join(dest_dir, name)
        with open(p, "wb") as out:
            shutil.copyfileobj(f.file, out)
        paths[f.filename] = p
    return {"ok": True, "session": sess, "dir": dest_dir, "count": len(paths), "paths": paths}


@app.get("/aplus/status")
def status(x_api_key: str = Header(default="")):
    _check(x_api_key)
    with _state_lock:
        _clear_finished_process()
        busy = bool(_current_process and _current_process.is_alive())
        started = _current_task.get("started_at")
        name = _current_task.get("name") if busy else None
    return {
        "ok": True,
        "busy": busy,
        "name": name,
        "running_seconds": int(time.time() - started) if busy and started else 0,
        "timeout_seconds": REQUEST_TIMEOUT_SECONDS,
    }


def _reset_ziniao_client():
    """任务超时后重置紫鸟,避免旧 webdriver 会话继续占店铺。"""
    import yaml
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "config.yaml")) as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    try:
        z.exit_client()
    except Exception:
        try:
            z.kill_client()
        except Exception:
            pass


def _worker_create(spec_data, out):
    try:
        out.put({"kind": "result", "payload": create_aplus(spec_data)})
    except Exception as e:
        out.put({
            "kind": "error",
            "payload": {"ok": False, "error": str(e), "traceback": traceback.format_exc(), "modules": []},
        })


def _clear_finished_process():
    global _current_process
    if _current_process and not _current_process.is_alive():
        _current_process.join(timeout=0.2)
        _current_process = None
        _current_task.update({"name": None, "started_at": None})


@app.post("/aplus/create")
def create(spec: Spec, x_api_key: str = Header(default="")):
    global _current_process
    _check(x_api_key)
    out = _ctx.Queue(maxsize=1)
    proc = _ctx.Process(target=_worker_create, args=(spec.model_dump(), out), daemon=True)
    with _state_lock:
        _clear_finished_process()
        if _current_process and _current_process.is_alive():
            started = _current_task.get("started_at")
            seconds = int(time.time() - started) if started else 0
            raise HTTPException(
                status_code=409,
                detail=f"正在处理另一个创建任务({seconds}s): {_current_task.get('name') or '-'},请稍后重试"
            )
        _current_process = proc
        _current_task.update({"name": spec.name, "started_at": time.time()})
        proc.start()

    proc.join(timeout=REQUEST_TIMEOUT_SECONDS)
    if proc.is_alive():
        proc.terminate()
        proc.join(timeout=10)
        if proc.is_alive():
            proc.kill()
            proc.join(timeout=5)
        _reset_ziniao_client()
        with _state_lock:
            _current_process = None
            _current_task.update({"name": None, "started_at": None})
        return {
            "ok": False,
            "error": f"创建任务超过 {REQUEST_TIMEOUT_SECONDS}s 已自动中止并重置紫鸟,请重新发起",
            "name": spec.name,
            "modules": [],
        }

    try:
        msg = out.get(timeout=10)
    except Empty:
        msg = {"kind": "error", "payload": {"ok": False, "error": "创建进程已结束但没有返回结果", "modules": []}}

    with _state_lock:
        _current_process = None
        _current_task.update({"name": None, "started_at": None})
    return msg.get("payload")

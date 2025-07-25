#!/usr/bin/env python3

# Clash Subscription Bridge (single‑URL, fixed endpoint)
# 逻辑源自 Clash‑Verge v1.3.8

import sys, time, yaml, requests
from urllib.parse import urlparse
from fastapi import FastAPI, Response
import uvicorn

# ---- 配置 ----
PORT        = 18518                          # 低冲突用户端口
ENDPOINT    = "/sub.yaml"                    # 固定路径
UA          = "Clash-Verge/1.3.8 (+https://github.com/zzzgydi/clash-verge)"
TIMEOUT     = 20
MAX_RETRY   = 3
# --------------

def fetch_yaml(url: str) -> str:
    print(f"正在下载订阅: {url}")
    """下载并校验订阅 YAML（保持 v1.3.8 逻辑）"""
    if urlparse(url).scheme not in ("http", "https"):
        raise ValueError("只接受 http/https 订阅链接")
    sess = requests.Session()
    sess.headers.update({"User-Agent": UA})
    verify = True
    for attempt in range(1, MAX_RETRY + 1):
        try:
            r = sess.get(url, timeout=TIMEOUT, verify=verify, allow_redirects=True)
            r.raise_for_status()
            text = r.text
            data = yaml.safe_load(text)
            if not isinstance(data, dict) or "proxies" not in data:
                raise ValueError("订阅内容不包含 'proxies' 字段")
            return text
        except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as e:
            if verify:        # 首次 TLS 失败 → 忽略证书再试
                verify = False
                continue
            elif attempt < MAX_RETRY:
                time.sleep(2 ** attempt)    # 指数退避
                continue
            raise RuntimeError(f"下载失败: {e}")
        except Exception:
            raise
    raise RuntimeError("多次重试后仍失败")

def main():
    # —— Step 0: 读取用户输入并抓取一次 ——
    try:
        url = input("输入订阅 URL: ").strip()
        yaml_text = fetch_yaml(url)
        print("订阅抓取成功，服务启动中 …  url: http://127.0.0.1:18518/sub.yaml")
    except Exception as exc:
        sys.stderr.write(f"初始化失败: {exc}\n")
        sys.exit(1)

    # —— Step 1: 启动 FastAPI 服务，固定端点返回缓存内容 ——
    app = FastAPI(title="Clash Subscription Bridge")

    @app.get(ENDPOINT)
    async def serve_yaml():
        return Response(yaml_text, media_type="application/yaml")

    @app.get("/")
    async def index():
        return {"msg": f"桥接服务运行中；订阅地址: http://127.0.0.1:{PORT}{ENDPOINT}"}

    uvicorn.run(app, host="127.0.0.1", port=PORT)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Clash‑Verge v1.3.8 订阅下载（精简 Python 版）

- 支持 http/https，优先 https；
- 失败后自动关闭证书校验再次尝试（等价于 v1.3.8 中
  `danger_accept_invalid_certs(true)` 的 fallback）；
- 校验 YAML 并确保包含 `proxies:` 字段；
- 最多重试 3 次。

# pip install requests PyYAML

"""
import sys
import time
import yaml
import requests
from urllib.parse import urlparse

# -------- 可按需调整的一些常量 --------
UA = "Clash-Verge/1.3.8 (+https://github.com/zzzgydi/clash-verge)"   # 同 v1.3.8 请求头:contentReference[oaicite:0]{index=0}
TIMEOUT = 20         # 单次网络超时
MAX_RETRY = 3        # 最大重试次数
# -----------------------------------

def fetch_subscription(url: str) -> str:
    """
    按 v1.3.8 逻辑下载订阅并返回纯文本。
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("只支持 http/https 订阅地址")

    session = requests.Session()
    session.headers.update({"User-Agent": UA})

    verify = True    # 第一次严格验证 TLS
    for attempt in range(1, MAX_RETRY + 1):
        try:
            resp = session.get(url, timeout=TIMEOUT, verify=verify, allow_redirects=True)
            resp.raise_for_status()
            text = resp.text

            # YAML 基本合法性 & proxies 字段检查
            try:
                doc = yaml.safe_load(text)
                if not isinstance(doc, dict) or "proxies" not in doc:
                    raise ValueError("订阅内容缺少 'proxies' 字段")
            except yaml.YAMLError as e:
                raise ValueError(f"订阅内容 YAML 解析失败: {e}") from None

            return text

        except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as net_err:
            if verify:                # 第一次 TLS 失败就关验证再试
                verify = False
                continue              # 等价于 Rust 版的 fallback
            elif attempt < MAX_RETRY: # 其他网络错误做指数退避重试
                time.sleep(2 ** attempt)
                continue
            else:
                raise net_err         # 最终仍失败就抛给调用者
        except Exception:
            raise                    # 其他异常不做吞并，直接抛出

def main() -> None:
    url = input("请输入 HTTPS 订阅链接: ").strip()
    try:
        content = fetch_subscription(url)
        print("\n=== 订阅内容开始 ===\n")
        print(content)
        print("=== 订阅内容结束 ===")
    except Exception as e:
        sys.stderr.write(f"订阅获取失败: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()



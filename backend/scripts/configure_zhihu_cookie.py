"""自动校验并写入知乎 Cookie 到 backend/.env。

用法（在 backend 目录）：
    uv run python scripts/configure_zhihu_cookie.py "z_c0=...; d_c0=...; __zse_ck=..."

或带 --apply 直接写入：
    uv run python scripts/configure_zhihu_cookie.py --apply "z_c0=..."

不传参数时从 stdin 读取整行（便于从浏览器粘贴，避免中转转录损坏）。
"""
from __future__ import annotations

import base64
import datetime as _dt
import re
import sys
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


def _check_cookie(cookie: str) -> tuple[bool, str]:
    """校验 cookie 字符串：z_c0 的 92: 段与 d_c0 的 base64 是否合法。

    返回 (ok, 详情)。合法 base64 长度须为 4 的倍数。
    """
    problems = []
    seen = set()
    for part in cookie.split(";"):
        part = part.strip()
        if not part:
            continue
        key, _, val = part.partition("=")
        seen.add(key)
        if key == "z_c0":
            m = re.search(r"92:([A-Za-z0-9+/]+)", val)
            if not m:
                problems.append("z_c0 缺少 '92:' base64 段")
                continue
            seg = m.group(1)
            pad = "=" * (4 - len(seg) % 4) if len(seg) % 4 else ""
            try:
                base64.b64decode(seg + pad, validate=True)
            except Exception as e:
                problems.append(f"z_c0 base64 非法 (len={len(seg)}, mod4={len(seg)%4}): {e}")
        elif key == "d_c0":
            seg = val.split("|", 1)[0]
            pad = "=" * (4 - len(seg) % 4) if len(seg) % 4 else ""
            try:
                base64.b64decode(seg + pad, validate=True)
            except Exception:
                problems.append("d_c0 base64 非法")
    for required in ("z_c0", "d_c0", "__zse_ck"):
        if required not in seen:
            problems.append(f"缺少 {required}")
    return (not problems, "; ".join(problems) if problems else "三组 Cookie 均合法")


def _timestamp_info(z_c0_value: str) -> str:
    """解析 z_c0 内的 '10:{unix}' 时间戳，返回 (日期, 距今天数) 提示。

    zh 的 z_c0 通常含一个签发/有效时间戳。若该项明显早于今天，
    强烈提示 cookie 可能已过期——这是判断 cookie 是否「取对了」的判据。
    """
    m = re.search(r"10:(\d{10})", z_c0_value)
    if not m:
        return "z_c0 未找到 '10:' 时间戳（格式异常）"
    ts = int(m.group(1))
    dt = _dt.datetime.fromtimestamp(ts, _dt.timezone.utc)
    now = _dt.datetime.now(_dt.timezone.utc)
    days = (now - dt).days
    fresh = "（近时，应有效）" if days <= 1 else "（★ 时间戳偏旧，需确认是否已过期）"
    return f"z_c0 时间戳={dt:%Y-%m-%d %H:%M} UTC，距今 {days} 天 {fresh}"


def main() -> None:
    args = sys.argv[1:]
    apply = "--apply" in args
    args = [a for a in args if a != "--apply"]

    if args:
        cookie = args[0]
    else:
        print("粘贴完整 Cookie（z_c0=...; d_c0=...; __zse_ck=...），回车结束：")
        cookie = sys.stdin.readline().strip()

    ok, detail = _check_cookie(cookie)
    print(f"校验: {'[OK] 通过' if ok else '[FAIL] 失败'} - {detail}")
    # z_c0 时间戳新鲜度提示（判断 cookie 是否「取对了」的判据）
    zc0_val = next(
        (p.partition("=")[2] for p in cookie.split(";") if p.strip().startswith("z_c0=")),
        "",
    )
    if zc0_val:
        print(_timestamp_info(zc0_val))
    if not ok:
        sys.exit(1)

    if not apply:
        print("Cookie 合法但未写入（未带 --apply）。用 --apply 参数写入。")
        return

    # 更新 .env 的 ZHIHU_COOKIES 行，保留其余内容
    text = ENV_PATH.read_text(encoding="utf-8")
    if "ZHIHU_COOKIES=" in text:
        text = re.sub(
            r"^ZHIHU_COOKIES=.*$",
            lambda _: f"ZHIHU_COOKIES='{cookie}'",
            text,
            flags=re.MULTILINE,
        )
    else:
        text += f"\n# Zhihu 配置（浏览器登录 zhihu.com 后复制的 Cookie）\nZHIHU_COOKIES='{cookie}'\n"
    ENV_PATH.write_text(text, encoding="utf-8")
    print(f"已写入 {ENV_PATH}")


if __name__ == "__main__":
    main()

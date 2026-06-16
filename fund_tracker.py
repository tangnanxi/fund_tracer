#!/usr/bin/env python3
"""
基金实时估算涨跌查询工具
数据来源：天天基金网（East Money）公开接口
"""

import json
import re
import sys
import urllib.request
from pathlib import Path
from datetime import datetime

# Windows CMD/PowerShell 默认可能是 GBK，强制用 UTF-8 输出中文
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


API_URL = "https://fundgz.1234567.com.cn/js/{code}.js"


def fetch_fund(code: str) -> dict | None:
    """查询单只基金的实时估算数据。"""
    url = API_URL.format(code=code)
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://fund.eastmoney.com/",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            text = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[{code}] 网络请求失败: {e}")
        return None

    # 接口返回的是 JSONP: jsonpgz({...});
    match = re.search(r"jsonpgz\((\{.*?\})\);", text)
    if not match:
        print(f"[{code}] 无法解析返回数据")
        return None

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        print(f"[{code}] JSON 解析失败")
        return None

    return data


def colorize(value: float) -> str:
    """按 A 股习惯：红涨绿跌。Windows 终端可能不支持 emoji，用 ASCII 标记。"""
    if value > 0:
        return f"+{value:.2f}% [UP]"
    elif value < 0:
        return f"{value:.2f}% [DOWN]"
    else:
        return f"{value:.2f}% [FLAT]"


def load_codes_from_file(path: Path) -> list[str]:
    codes = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        codes.append(line.split()[0])
    return codes


def main():
    if len(sys.argv) < 2:
        config = Path(__file__).with_name("funds.txt")
        if config.exists():
            codes = load_codes_from_file(config)
            if not codes:
                print(f"配置文件 {config} 中没有找到基金代码")
                sys.exit(1)
        else:
            print("用法: python fund_tracker.py <基金代码1> [基金代码2] ...")
            print(f"或在 {config} 中写入基金代码，每行一个")
            sys.exit(1)
    else:
        codes = sys.argv[1:]

    print(f"\n查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"共 {len(codes)} 只基金\n")
    print(f"{'基金代码':<10}{'基金名称':<30}{'最新净值':>12}{'估算净值':>12}{'估算涨跌':>14}{'估值时间':>22}")
    print("-" * 100)

    total_change = 0.0
    valid_count = 0

    for code in codes:
        data = fetch_fund(code)
        if not data:
            continue

        name = data.get("name", "-")[:28]
        dwjz = data.get("dwjz", "-")
        gsz = data.get("gsz", "-")
        gszzl = data.get("gszzl", "0")
        gztime = data.get("gztime", "-")

        try:
            change = float(gszzl)
        except ValueError:
            change = 0.0

        total_change += change
        valid_count += 1

        print(f"{code:<10}{name:<30}{str(dwjz):>12}{str(gsz):>12}{colorize(change):>18}{gztime:>22}")

    if valid_count:
        avg = total_change / valid_count
        print("-" * 100)
        print(f"平均估算涨跌: {colorize(avg)}\n")


if __name__ == "__main__":
    main()

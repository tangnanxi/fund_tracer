#!/usr/bin/env python3
"""
基金持仓实时估算收益查询工具
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
ENCODING = "utf-8"


def get_skill_dir() -> Path:
    return Path(__file__).resolve().parent


def get_holdings_path() -> Path:
    return get_skill_dir() / "holdings.json"


def get_history_path() -> Path:
    return get_skill_dir() / "history.json"


def get_funds_txt_path() -> Path:
    return get_skill_dir() / "funds.txt"


def load_json(path: Path, default=None):
    if default is None:
        default = {}
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding=ENCODING))
    except (json.JSONDecodeError, OSError):
        return default


def save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding=ENCODING)


def load_funds_txt(path: Path) -> list[str]:
    codes = []
    if not path.exists():
        return codes
    for line in path.read_text(encoding=ENCODING).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        codes.append(line.split()[0])
    return codes


def fetch_fund(code: str) -> dict | None:
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


def make_holding(code: str, fund_data: dict | None) -> dict:
    """生成一份默认持仓记录。"""
    cost_price = 0.0
    if fund_data:
        try:
            cost_price = float(fund_data.get("gsz", "0") or 0)
        except (ValueError, TypeError):
            cost_price = 0.0
    return {
        "code": code,
        "shares": 0.0,
        "cost_price": cost_price,
    }


def init_holdings(codes: list[str], fund_data: dict[str, dict]) -> dict:
    return {
        "holdings": [make_holding(code, fund_data.get(code)) for code in codes]
    }


def merge_holdings(existing: dict, codes: list[str], fund_data: dict[str, dict]) -> dict:
    """保留用户已配置的 shares/cost_price，只追加新基金代码；
    若某条记录的 cost_price 仍为 0，则用当前估算净值自动补全。"""
    holdings_list = existing.get("holdings", [])
    if not isinstance(holdings_list, list):
        holdings_list = []

    existing_codes = {
        h["code"] for h in holdings_list
        if isinstance(h, dict) and h.get("code")
    }

    # 补全已有记录中 cost_price 为 0 的情况
    for holding in holdings_list:
        if not isinstance(holding, dict):
            continue
        code = holding.get("code")
        if code and parse_float(holding.get("cost_price")) == 0:
            data = fund_data.get(code)
            if data:
                holding["cost_price"] = parse_float(data.get("gsz"))

    # 追加新基金代码
    for code in codes:
        if code in existing_codes:
            continue
        holdings_list.append(make_holding(code, fund_data.get(code)))

    return {"holdings": holdings_list}


def parse_float(value, default: float = 0.0) -> float:
    try:
        return float(value or default)
    except (ValueError, TypeError):
        return default


def colorize_pct(value: float) -> str:
    if value > 0:
        return f"+{value:.2f}%"
    elif value < 0:
        return f"{value:.2f}%"
    else:
        return f"{value:.2f}%"


def colorize_money(value: float) -> str:
    if value > 0:
        return f"+{value:.2f}"
    elif value < 0:
        return f"{value:.2f}"
    else:
        return f"{value:.2f}"


def get_trading_date(gztime: str) -> str:
    """从估值时间中提取日期，如 '2026-06-17 15:00' -> '2026-06-17'。"""
    if gztime and len(gztime) >= 10:
        return gztime[:10]
    return datetime.now().strftime("%Y-%m-%d")


def update_history(history: dict, code: str, date: str, nav: float, change_pct: float):
    history.setdefault("history", {})
    history["history"].setdefault(code, [])
    records = history["history"][code]

    new_record = {"date": date, "nav": nav, "change_pct": change_pct}
    if records and records[-1].get("date") == date:
        records[-1] = new_record
    else:
        records.append(new_record)


def main():
    skill_dir = get_skill_dir()
    holdings_path = get_holdings_path()
    history_path = get_history_path()
    funds_txt_path = get_funds_txt_path()

    # 1. 读取基金代码
    codes_from_txt = load_funds_txt(funds_txt_path)
    if not codes_from_txt and not holdings_path.exists():
        print("用法: python fund_tracker.py <基金代码1> [基金代码2] ...")
        print(f"或在 {funds_txt_path} 中写入基金代码，每行一个")
        sys.exit(1)

    # 2. 先获取基金数据（用于初始化和补齐 holdings）
    fund_data = {}
    for code in codes_from_txt:
        data = fetch_fund(code)
        if data:
            fund_data[code] = data

    # 3. 初始化/合并 holdings.json
    if holdings_path.exists():
        existing = load_json(holdings_path, {"holdings": []})
        holdings = merge_holdings(existing, codes_from_txt, fund_data)
    else:
        holdings = init_holdings(codes_from_txt, fund_data)
        print(f"已生成持仓配置文件: {holdings_path}")
        print("请编辑该文件填入你的实际份额和成本价，然后重新运行。")
        print("如果你不需要计算收益，也可将 shares 保持为 0。\n")

    save_json(holdings_path, holdings)

    # 4. 加载历史净值
    history = load_json(history_path, {"history": {}})

    # 5. 输出表头
    holdings_list = holdings.get("holdings", [])
    print(f"\n查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"共 {len(holdings_list)} 只基金\n")

    headers = (
        f"{'基金代码':<10}"
        f"{'基金名称':<30}"
        f"{'份额':>12}"
        f"{'最新净值':>12}"
        f"{'估算净值':>12}"
        f"{'估算涨跌':>12}"
        f"{'当日预估收益':>16}"
        f"{'持仓市值':>14}"
        f"{'累计收益':>14}"
        f"{'估值时间':>20}"
    )
    print(headers)
    print("-" * len(headers))

    total_market_value = 0.0
    total_daily_profit = 0.0
    total_holding_profit = 0.0
    valid_count = 0

    for holding in holdings_list:
        if not isinstance(holding, dict):
            continue

        code = holding.get("code", "")
        shares = parse_float(holding.get("shares", 0))
        cost_price = parse_float(holding.get("cost_price", 0))

        data = fund_data.get(code) or fetch_fund(code)
        if not data:
            continue

        name = data.get("name", "-")[:28]
        dwjz = data.get("dwjz", "-")
        gsz = data.get("gsz", "-")
        gszzl = data.get("gszzl", "0")
        gztime = data.get("gztime", "-")

        dwjz_f = parse_float(dwjz)
        gsz_f = parse_float(gsz)
        gszzl_f = parse_float(gszzl)

        daily_profit = dwjz_f * shares * (gszzl_f / 100)
        market_value = gsz_f * shares
        holding_profit = (gsz_f - cost_price) * shares

        total_market_value += market_value
        total_daily_profit += daily_profit
        total_holding_profit += holding_profit
        valid_count += 1

        date = get_trading_date(gztime)
        update_history(history, code, date, gsz_f, gszzl_f)

        print(
            f"{code:<10}"
            f"{name:<30}"
            f"{shares:>12.2f}"
            f"{str(dwjz):>12}"
            f"{str(gsz):>12}"
            f"{colorize_pct(gszzl_f):>14}"
            f"{colorize_money(daily_profit):>16}"
            f"{market_value:>14.2f}"
            f"{colorize_money(holding_profit):>14}"
            f"{gztime:>20}"
        )

    if valid_count:
        print("-" * len(headers))
        print(f"总市值:          {total_market_value:>10.2f}")
        print(f"当日总预估收益:  {colorize_money(total_daily_profit):>12}")
        print(f"累计总收益:      {colorize_money(total_holding_profit):>12}\n")

    # 6. 保存历史净值
    save_json(history_path, history)


if __name__ == "__main__":
    main()

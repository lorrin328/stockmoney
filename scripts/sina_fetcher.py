#!/usr/bin/env python3
"""
新浪财经行情数据拉取脚本
"""
import requests, csv, json, re, sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

SINA_HQ_URL = "http://hq.sinajs.cn/list={codes}"
HEADERS = {
    "Referer": "https://finance.sina.com.cn",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}

EXCHANGE_MAP = {
    "sh": "sh", "sz": "sz", "bj": "bj",
}

def normalize_code(code: str) -> str:
    code = code.strip().lower()
    if code.startswith(("sh", "sz", "bj")):
        return code
    if code.startswith("6") or code.startswith("000"):
        return f"sh{code}"
    if code.startswith(("0", "3", "399")):
        return f"sz{code}"
    if code.startswith(("4", "8")):
        return f"bj{code}"
    return f"sh{code}"

def fetch_quotes(codes: list[str]) -> dict[str, dict]:
    results = {}
    normalized = [normalize_code(c) for c in codes]
    for i in range(0, len(normalized), 800):
        batch = normalized[i:i+800]
        url = SINA_HQ_URL.format(codes=",".join(batch))
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.encoding = "gb2312"
        for line in resp.text.strip().split(";"):
            line = line.strip()
            if not line:
                continue
            m = re.match(r'var hq_str_(\w+)="(.*)"', line)
            if not m:
                continue
            code, data = m.group(1), m.group(2)
            if not data:
                continue
            results[code] = parse_quote(code, data.split(","))
    return results

def parse_quote(code: str, parts: list[str]) -> dict:
    is_index = code.startswith(("sh000", "sz399")) or len(parts) <= 33
    base = {
        "code": code,
        "name": parts[0],
        "prev_close": float(parts[2]) if len(parts) > 2 else None,
        "open": float(parts[1]) if len(parts) > 1 else None,
        "current": float(parts[3]) if len(parts) > 3 else None,
        "high": float(parts[4]) if len(parts) > 4 else None,
        "low": float(parts[5]) if len(parts) > 5 else None,
        "volume": int(parts[8]) if len(parts) > 8 else None,
        "amount": float(parts[9]) if len(parts) > 9 else None,
        "date": parts[30] if len(parts) > 30 else None,
        "time": parts[31] if len(parts) > 31 else None,
    }
    if is_index:
        base["prev_close"] = float(parts[1]) if len(parts) > 1 else None
        base["open"] = float(parts[2]) if len(parts) > 2 else None
    else:
        base.update({
            "bid1_price": float(parts[11]) if len(parts) > 11 else None,
            "bid1_vol": int(parts[10]) if len(parts) > 10 else None,
            "ask1_price": float(parts[21]) if len(parts) > 21 else None,
            "ask1_vol": int(parts[20]) if len(parts) > 20 else None,
        })
    return base

def save_csv(quotes: dict, filename: str = None):
    if not quotes:
        return
    if filename is None:
        filename = f"quotes_{datetime.now():%Y%m%d_%H%M%S}.csv"
    path = DATA_DIR / filename
    rows = list(quotes.values())
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"CSV saved: {path}")
    return path

def save_json(quotes: dict, filename: str = None):
    if filename is None:
        filename = f"quotes_{datetime.now():%Y%m%d_%H%M%S}.json"
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(quotes, f, ensure_ascii=False, indent=2)
    print(f"JSON saved: {path}")
    return path

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 sina_fetcher.py <code1> [code2] ...")
        print("  e.g. python3 sina_fetcher.py 600519 000858 sh000001")
        sys.exit(1)
    quotes = fetch_quotes(sys.argv[1:])
    for code, q in quotes.items():
        chg = ((q["current"] - q["prev_close"]) / q["prev_close"] * 100) if q.get("prev_close") else 0
        print(f"{q['name']:<8} {code:<10} {q['current']:<10.2f} {chg:+.2f}%")
    save_csv(quotes)
    save_json(quotes)

if __name__ == "__main__":
    main()

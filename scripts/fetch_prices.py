import requests, json, os
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
HEADERS = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", "Referer": "https://m.stock.naver.com/"}

def fetch_kr(code):
    url = f"https://m.stock.naver.com/api/stock/{code}/integration"
    r = requests.get(url, headers=HEADERS, timeout=10)
    data = r.json()
    # 현재가 파싱 (ETF 우선, 일반주식 fallback)
    etf = data.get("etfTabInfo", {})
    pi = etf.get("priceInfo", {})
    price = pi.get("closePrice") or pi.get("openPrice")
    if price: price = float(str(price).replace(",",""))
    prev_diff = pi.get("compareToPreviousClosePrice", "0")
    if prev_diff: prev_diff = float(str(prev_diff).replace(",","").replace("+",""))
    prev = (price - prev_diff) if price else None
    name = etf.get("etfName") or data.get("stockInfo",{}).get("stockName","")
    if not price:  # fallback
        si = data.get("stockInfo", {})
        price = float(str(si.get("currentPrice","0")).replace(",","")) or None
        prev = price
        name = si.get("stockName","")
    return {"price": price, "prev": prev, "name": name, "currency": "KRW", "ok": bool(price)}

def fetch_us(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    meta = r.json()["chart"]["result"][0]["meta"]
    price = meta.get("regularMarketPrice") or meta.get("previousClose")
    prev = meta.get("chartPreviousClose") or meta.get("previousClose") or price
    return {"price": price, "prev": prev, "name": meta.get("longName") or symbol, "currency": "USD", "ok": bool(price)}

tickers = json.load(open("tickers.json"))
results = {}
for code, info in tickers.items():
    try:
        res = fetch_kr(code) if info["market"]=="KR" else fetch_us(code)
    except Exception as e:
        res = {"ok": False, "error": str(e)}
    results[code] = {**info, **res}

output = {"updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"), "prices": results}
json.dump(output, open("prices.json","w"), ensure_ascii=False, indent=2)
print(f"Done: {len(results)} tickers updated")

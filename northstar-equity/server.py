"""Local NorthStar Equity server with a Screener data proxy."""

from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from html import unescape
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen
import json
import os
import re
import time


def fetch_url(request, timeout=12, attempts=3):
    last_error = None
    for attempt in range(attempts):
        try:
            return urlopen(request, timeout=timeout)
        except Exception as error:
            last_error = error
            if attempt + 1 < attempts:
                time.sleep(1.5 * (attempt + 1))
    raise last_error


class ScreenerParser(HTMLParser):
    """Extract visible text and table rows from a Screener company page."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.rows = []
        self.current_row = None
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.skip_depth += 1
        if tag == "tr":
            self.current_row = []

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self.skip_depth:
            self.skip_depth -= 1
        if tag == "tr" and self.current_row is not None:
            row = " ".join(self.current_row)
            if row:
                self.rows.append(row)
            self.current_row = None

    def handle_data(self, data):
        clean = " ".join(data.split())
        if not clean or self.skip_depth:
            return
        self.text_parts.append(clean)
        if self.current_row is not None:
            self.current_row.append(clean)

    @property
    def text(self):
        return " ".join(self.text_parts)


def number_after(label, text):
    pattern = rf"{re.escape(label)}\s*₹?\s*([\d,]+(?:\.\d+)?)"
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1) if match else None


def numeric_values(row):
    return [float(value.replace(",", "")) for value in re.findall(r"(?<![A-Za-z])[\d,]+(?:\.\d+)?", row)]


def latest_annual_series(rows, prefix):
    matches = [row for row in rows if row.lower().startswith(prefix.lower())]
    if not matches:
        return [], []
    row = matches[-1]
    values = numeric_values(row)
    labels = []
    row_index = rows.index(row)
    for previous_row in reversed(rows[:row_index]):
        candidate_labels = re.findall(r"Mar \d{4}", previous_row)
        if len(candidate_labels) >= len(values):
            labels = candidate_labels[-len(values):]
            break
    return labels[-5:], values[-5:]


def latest_ratio(rows, prefix):
    matches = [row for row in rows if row.lower().startswith(prefix.lower())]
    if not matches:
        return None
    values = numeric_values(matches[-1])
    return values[-1] if values else None


def parse_screener(symbol, include_peers=True):
    safe_symbol = re.sub(r"[^A-Za-z0-9_-]", "", symbol.upper())
    if not safe_symbol:
        raise ValueError("Enter a valid NSE symbol")

    url = f"https://www.screener.in/company/{safe_symbol}/consolidated/"
    request = Request(url, headers={"User-Agent": "NorthStar Equity academic dashboard"})
    with fetch_url(request, timeout=12) as response:
        html = response.read().decode("utf-8", errors="replace")

    parser = ScreenerParser()
    parser.feed(html)
    text = parser.text

    price = number_after("Current Price", text)
    if not price:
        standalone_url = f"https://www.screener.in/company/{safe_symbol}/"
        standalone_request = Request(standalone_url, headers={"User-Agent": "NorthStar Equity academic dashboard"})
        with fetch_url(standalone_request, timeout=12) as response:
            html = response.read().decode("utf-8", errors="replace")
        parser = ScreenerParser()
        parser.feed(html)
        text = parser.text
        url = standalone_url
        price = number_after("Current Price", text)
    market_cap = number_after("Market Cap", text)
    pe = number_after("Stock P/E", text)
    roce = number_after("ROCE", text)
    roe = number_after("ROE", text)
    quote_match = re.search(r"([+-]\s*\d+(?:\.\d+)?)%\s+(\d{1,2}\s+[A-Za-z]{3})\s+-\s+close price", text, re.IGNORECASE)
    daily_move = quote_match.group(1).replace(" ", "") + "%" if quote_match else "Unavailable"
    quote_date = quote_match.group(2) if quote_match else "Unavailable"
    heading_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    company = re.sub(r"<[^>]+>", "", heading_match.group(1)).strip() if heading_match else safe_symbol
    company = unescape(" ".join(company.split()))

    ccc_values = []
    ccc_labels = []
    for row in parser.rows:
        if row.lower().startswith("cash conversion cycle"):
            ccc_values = re.findall(r"\b\d+(?:\.\d+)?\b", row)
            for previous_row in reversed(parser.rows[:parser.rows.index(row)]):
                labels = re.findall(r"Mar \d{4}", previous_row)
                if len(labels) >= len(ccc_values):
                    ccc_labels = labels[-len(ccc_values):]
                    break
            break

    annual_labels, revenue_series = latest_annual_series(parser.rows, "Sales +")
    _, operating_profit_series = latest_annual_series(parser.rows, "Operating Profit")
    _, operating_margin_series = latest_annual_series(parser.rows, "OPM %")
    cashflow_labels, cashflow_series = latest_annual_series(parser.rows, "Cash from Operating Activity")
    _, debtor_series = latest_annual_series(parser.rows, "Debtor Days")
    _, inventory_series = latest_annual_series(parser.rows, "Inventory Days")
    _, payable_series = latest_annual_series(parser.rows, "Days Payable")
    _, ccc_series = latest_annual_series(parser.rows, "Cash Conversion Cycle")
    revenue_growth_match = re.search(r"Compounded Sales Growth.*?5 Years:\s*(\d+)%", text, re.IGNORECASE | re.DOTALL)
    revenue_growth = float(revenue_growth_match.group(1)) if revenue_growth_match else None
    debt_match = re.search(r"Borrowings \+[^\n]*", "\n".join(parser.rows), re.IGNORECASE)
    reserve_match = re.search(r"Reserves[^\n]*", "\n".join(parser.rows), re.IGNORECASE)
    debt_values = numeric_values(debt_match.group(0)) if debt_match else []
    reserve_values = numeric_values(reserve_match.group(0)) if reserve_match else []
    debt_equity = round(debt_values[-1] / reserve_values[-1], 2) if debt_values and reserve_values and reserve_values[-1] else None

    link_matches = re.findall(r'<a[^>]+href="/company/([^/]+)/[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
    link_symbols = {
        re.sub(r"<[^>]+>", "", name).strip().lower(): company_symbol
        for company_symbol, name in link_matches
    }
    peers = []
    for row in parser.rows:
        rank_match = re.match(r"\d+\.\s+(.+?)\s+[\d,]+(?:\.\d+)?\s+", row)
        values = re.findall(r"(?<![A-Za-z])[\d,]+(?:\.\d+)?", row)
        if not rank_match or len(values) < 10:
            continue
        peer_name = rank_match.group(1).strip()
        peer_symbol = link_symbols.get(peer_name.lower())
        if not peer_symbol or peer_symbol.upper() == safe_symbol:
            continue
        peer_values = [float(value.replace(",", "")) for value in values[1:]]
        peers.append({
            "name": peer_name,
            "symbol": peer_symbol.upper(),
            "price": peer_values[0],
            "pe": peer_values[1],
            "marketCap": peer_values[2],
            "roce": peer_values[8],
            "revenueGrowth": None,
            "operatingMargin": None,
            "roe": None,
            "debtEquity": None,
        })

    known_sector_peers = {
        "TCS": [("INFY", "Infosys Ltd"), ("HCLTECH", "HCL Technologies Ltd"), ("WIPRO", "Wipro Ltd"), ("TECHM", "Tech Mahindra Ltd"), ("PERSISTENT", "Persistent Systems Ltd")],
        "INFY": [("TCS", "Tata Consultancy Services Ltd"), ("HCLTECH", "HCL Technologies Ltd"), ("WIPRO", "Wipro Ltd"), ("TECHM", "Tech Mahindra Ltd"), ("PERSISTENT", "Persistent Systems Ltd")],
        "HINDUNILVR": [("ITC", "ITC Ltd"), ("NESTLEIND", "Nestle India Ltd"), ("BRITANNIA", "Britannia Industries Ltd"), ("DABUR", "Dabur India Ltd"), ("MARICO", "Marico Ltd")],
    }
    if include_peers and not peers and safe_symbol in known_sector_peers:
        for peer_symbol, peer_name in known_sector_peers[safe_symbol]:
            try:
                peer_data = parse_screener(peer_symbol, include_peers=False)
                peers.append({
                    "name": peer_name,
                    "symbol": peer_symbol,
                    "price": peer_data["metrics"]["price"],
                    "pe": peer_data["metrics"]["pe"],
                    "marketCap": peer_data["metrics"]["marketCap"],
                    "roce": peer_data["metrics"]["roce"],
                    "revenueGrowth": peer_data["metrics"]["revenueGrowth"],
                    "operatingMargin": peer_data["metrics"]["operatingMargin"],
                    "roe": peer_data["metrics"]["roe"],
                    "debtEquity": peer_data["metrics"]["debtEquity"],
                })
            except Exception:
                continue

    if include_peers and safe_symbol in known_sector_peers and len(peers) < 5:
        existing_symbols = {peer["symbol"] for peer in peers}
        for peer_symbol, peer_name in known_sector_peers[safe_symbol]:
            if len(peers) >= 5 or peer_symbol in existing_symbols:
                continue
            try:
                peer_data = parse_screener(peer_symbol, include_peers=False)
                peers.append({
                    "name": peer_name,
                    "symbol": peer_symbol,
                    "price": peer_data["metrics"]["price"],
                    "pe": peer_data["metrics"]["pe"],
                    "marketCap": peer_data["metrics"]["marketCap"],
                    "roce": peer_data["metrics"]["roce"],
                    "revenueGrowth": peer_data["metrics"]["revenueGrowth"],
                    "operatingMargin": peer_data["metrics"]["operatingMargin"],
                    "roe": peer_data["metrics"]["roe"],
                    "debtEquity": peer_data["metrics"]["debtEquity"],
                })
                existing_symbols.add(peer_symbol)
            except Exception:
                continue

    if include_peers and not peers:
        market_paths = re.findall(r'<a[^>]+href="(/market/[^"]+)"', html, re.IGNORECASE)
        if market_paths:
            industry_url = "https://www.screener.in" + market_paths[-1]
            try:
                market_request = Request(industry_url, headers={"User-Agent": "NorthStar Equity academic dashboard"})
                with fetch_url(market_request, timeout=12) as market_response:
                    market_html = market_response.read().decode("utf-8", errors="replace")
                candidate_links = re.findall(r'<a[^>]+href="/company/([A-Za-z0-9_-]+)(?:/consolidated)?/"[^>]*>(.*?)</a>', market_html, re.IGNORECASE | re.DOTALL)
                seen_symbols = {safe_symbol}
                for peer_symbol, peer_name_markup in candidate_links:
                    peer_symbol = peer_symbol.upper()
                    if peer_symbol in seen_symbols or len(peers) >= 5:
                        continue
                    seen_symbols.add(peer_symbol)
                    try:
                        peer_data = parse_screener(peer_symbol, include_peers=False)
                        peer_name = unescape(re.sub(r"<[^>]+>", "", peer_name_markup)).strip()
                        peer_metrics = peer_data["metrics"]
                        peers.append({
                            "name": peer_name or peer_data["company"],
                            "symbol": peer_symbol,
                            "price": peer_metrics["price"],
                            "pe": peer_metrics["pe"],
                            "marketCap": peer_metrics["marketCap"],
                            "roce": peer_metrics["roce"],
                            "revenueGrowth": peer_metrics["revenueGrowth"],
                            "operatingMargin": peer_metrics["operatingMargin"],
                            "roe": peer_metrics["roe"],
                            "debtEquity": peer_metrics["debtEquity"],
                        })
                    except Exception:
                        continue
            except Exception:
                pass

    peer_average = {}
    if peers:
        peer_average = {
            "price": round(sum(peer["price"] for peer in peers) / len(peers), 2),
            "pe": round(sum(peer["pe"] for peer in peers) / len(peers), 2),
            "marketCap": round(sum(peer["marketCap"] for peer in peers) / len(peers), 2),
            "roce": round(sum(peer["roce"] for peer in peers) / len(peers), 2),
            "revenueGrowth": round(sum(peer["revenueGrowth"] for peer in peers if peer.get("revenueGrowth") is not None) / max(1, len([peer for peer in peers if peer.get("revenueGrowth") is not None])), 2),
            "operatingMargin": round(sum(peer["operatingMargin"] for peer in peers if peer.get("operatingMargin") is not None) / max(1, len([peer for peer in peers if peer.get("operatingMargin") is not None])), 2),
            "roe": round(sum(peer["roe"] for peer in peers if peer.get("roe") is not None) / max(1, len([peer for peer in peers if peer.get("roe") is not None])), 2),
            "debtEquity": round(sum(peer["debtEquity"] for peer in peers if peer.get("debtEquity") is not None) / max(1, len([peer for peer in peers if peer.get("debtEquity") is not None])), 2),
        }

    sector_links = re.findall(r'<a[^>]+href="/market/[^\"]+"[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
    sector_labels = [unescape(re.sub(r"<[^>]+>", "", label)).strip() for label in sector_links]
    sector = sector_labels[0] if sector_labels else "Sector classification unavailable"

    if not price:
        raise RuntimeError("Screener returned no current price for this symbol")

    return {
        "symbol": safe_symbol,
        "sourceUrl": url,
        "company": company,
        "price": f"Rs {price}",
        "marketCap": f"Rs {market_cap} Cr" if market_cap else "Unavailable",
        "pe": pe or "Unavailable",
        "roce": f"{roce}%" if roce else "Unavailable",
        "roe": f"{roe}%" if roe else "Unavailable",
        "dailyMove": daily_move,
        "quoteDate": quote_date,
        "metrics": {
            "price": float(price.replace(",", "")),
            "pe": float(pe) if pe else None,
            "marketCap": float(market_cap.replace(",", "")) if market_cap else None,
            "roce": float(roce) if roce else None,
            "roe": float(roe) if roe else None,
            "revenueGrowth": revenue_growth,
            "operatingMargin": operating_margin_series[-1] if operating_margin_series else None,
            "debtEquity": debt_equity,
        },
        "ccc": [f"{value} days" for value in ccc_values[-5:]],
        "cccLabels": ccc_labels[-5:] if ccc_labels else ["Latest 1", "Latest 2", "Latest 3", "Latest 4", "Latest 5"],
        "sector": sector,
        "peerAverage": peer_average,
        "peers": peers[:6],
        "financialSeries": {
            "labels": annual_labels or cashflow_labels,
            "revenue": revenue_series,
            "ebitda": operating_profit_series,
            "cashFlowLabels": cashflow_labels,
            "cashFlow": cashflow_series,
            "operatingMargin": operating_margin_series,
        },
        "workingCapital": {
            "debtorDays": debtor_series[-1] if debtor_series else None,
            "inventoryDays": inventory_series[-1] if inventory_series else None,
            "daysPayable": payable_series[-1] if payable_series else None,
            "cashConversionCycle": ccc_series[-1] if ccc_series else None,
        },
    }


def search_screener(query):
    search_term = query.strip()
    if not search_term:
        return []
    url = f"https://www.screener.in/api/company/search/?q={search_term}"
    request = Request(url, headers={"User-Agent": "NorthStar Equity academic dashboard"})
    with fetch_url(request, timeout=8) as response:
        results = json.loads(response.read().decode("utf-8"))

    suggestions = []
    for result in results[:8]:
        match = re.search(r"/company/([^/]+)/", result.get("url", ""))
        if match:
            suggestions.append({"symbol": match.group(1), "name": result.get("name", "")})
    return suggestions


class NorthStarHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def do_POST(self):
        self.send_error(404)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_json({"ok": True, "provider": "live-screener"})
            return
        if parsed.path == "/api/search":
            query = parse_qs(parsed.query).get("q", [""])[0]
            try:
                self.send_json({"ok": True, "data": search_screener(query)})
            except Exception as error:
                self.send_json({"ok": False, "error": str(error)}, status=502)
            return
        if parsed.path == "/api/company":
            symbol = parse_qs(parsed.query).get("symbol", ["TCS"])[0]
            try:
                payload = {"ok": True, "data": parse_screener(symbol)}
                self.send_json(payload)
            except Exception as error:
                self.send_json({"ok": False, "error": str(error)}, status=502)
            return
        super().do_GET()

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    port = int(os.environ.get("PORT", "8005"))
    host = os.environ.get("HOST", "127.0.0.1")
    print(f"NorthStar Equity running at http://localhost:{port}")
    print("Screener proxy: /api/company?symbol=TCS")
    ThreadingHTTPServer((host, port), NorthStarHandler).serve_forever()

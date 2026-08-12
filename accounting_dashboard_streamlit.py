import streamlit as st
import pandas as pd
import requests
from html.parser import HTMLParser

st.set_page_config(
    page_title="Screener.in Company Analyzer",
    page_icon="📈",
    layout="wide",
)

st.markdown("""
    <style>
        :root{--accent:#0f62fe; --muted:#6b778c; --card:#ffffff; --bg:#f6f8fb}
        body {font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; background: var(--bg);} 
        .stApp { padding: 1.25rem; }
        .header { display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:1rem 1.25rem; border-radius:12px; background: linear-gradient(90deg, rgba(15,98,254,0.08), rgba(50,130,184,0.04)); box-shadow: 0 6px 18px rgba(16,24,40,0.04); margin-bottom:1rem }
        .title {font-size:1.75rem; font-weight:800; color: #072b6b; margin:0}
        .subtitle {font-size:0.95rem; color:var(--muted); margin:0}
        .section-header {font-size:1.1rem; color:var(--accent); margin-top:1rem; margin-bottom:0.5rem; font-weight:700}
        .company-display {text-align:center; margin-top:1rem; margin-bottom:1rem; font-size:1.15rem; color:#0f9d58; font-weight:700}
        .company-badge { display:inline-flex; align-items:center; padding:0.35rem 0.6rem; border-radius:999px; background:#0f9d58; color:#fff; font-size:0.85rem; box-shadow:0 8px 20px rgba(15,157,88,0.12)}
        .card { background:var(--card); border-radius:12px; padding:1rem; box-shadow: 0 6px 18px rgba(16,24,40,0.04); }
        .metrics-row .stMetric { border-radius:10px; padding:0.75rem; background: linear-gradient(180deg, rgba(255,255,255,0.8), rgba(247,250,255,0.8));}
        .reasons { padding:0.75rem; border-radius:10px; background: linear-gradient(90deg, rgba(15,98,254,0.03), rgba(15,98,254,0.01)); }
        .risks { padding:0.75rem; border-radius:10px; background: linear-gradient(90deg, rgba(255,70,70,0.03), rgba(255,70,70,0.01)); }
        .sidebar .stButton>button { border-radius:8px }
        .small-muted { color:var(--muted); font-size:0.9rem }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="header"><div><div class="title">📊 Screener.in Company Analyzer</div><div class="subtitle">Enter a Screener.in ticker. Values shown are 1-year; rupee amounts are treated as ₹ Crore-scale from Screener.</div></div><div style="text-align:right"><div class="small-muted">Live: Screener + optional MCP</div></div></div>', unsafe_allow_html=True)

sample_companies = [
    "TCS", "RELIANCE", "INFY", "HDFC", "WIPRO", "LT", "ICICIBANK",
    "NESTLEIND", "BHARTIARTL", "SBIN", "ONGC", "ITC", "TITAN", "MARUTI",
    "HINDUNILVR", "ASIANPAINT", "KOTAKBANK", "JSWSTEEL", "VEDL",
    "HDFCBANK", "AXISBANK", "SUNPHARMA", "BAJAJ-AUTO", "TECHM",
    "COALINDIA", "MARICO", "SBILIFE", "UPL", "ADANIENT", "ADANIPORTS",
    "BRITANNIA", "CIPLA", "DIVISLAB", "DRREDDY", "EICHERMOT", "GRASIM",
    "HCLTECH", "HDFCLIFE", "HCLTECH", "HAVELLS", "ICICIPRULI", "LTIM",
    "M&M", "PIDILITIND", "SHREECEM", "TATAMOTORS", "TATACONSUM", "TATASTEEL",
    "ULTRACEMCO", "ZEEL", "BHARATFORG", "BANDHANBNK", "DLF",
    "YESBANK", "UNIONBANK",
]

avoid_companies = ["YESBANK", "ADANIPORTS"]

sample_company_data = {
    "TCS": {
        "revenue": 175000.0,
        "prior_revenue": 158000.0,
        "cogs": 72000.0,
        "operating_profit": 34500.0,
        "ebitda": 41000.0,
        "eps": 115.0,
        "cfo": 38000.0,
        "cfi": -8200.0,
        "cff": -7100.0,
        "inventory": 7500.0,
        "receivables": 12400.0,
        "bse_code": "532540",
    },
    "RELIANCE": {
        "revenue": 680000.0,
        "prior_revenue": 630000.0,
        "cogs": 405000.0,
        "operating_profit": 62000.0,
        "ebitda": 118000.0,
        "eps": 100.0,
        "cfo": 83000.0,
        "cfi": -52000.0,
        "cff": -22000.0,
        "inventory": 43000.0,
        "receivables": 29500.0,
        "bse_code": "500325",
    },
    "INFY": {
        "revenue": 180000.0,
        "prior_revenue": 163000.0,
        "cogs": 88000.0,
        "operating_profit": 29000.0,
        "ebitda": 34000.0,
        "eps": 24.0,
        "cfo": 27000.0,
        "cfi": -7000.0,
        "cff": -4900.0,
        "inventory": 9200.0,
        "receivables": 15200.0,
        "bse_code": "500209",
    },
    "HDFC": {
        "revenue": 125000.0,
        "prior_revenue": 118000.0,
        "cogs": 52000.0,
        "operating_profit": 28000.0,
        "ebitda": 33000.0,
        "eps": 35.0,
        "cfo": 24000.0,
        "cfi": -13000.0,
        "cff": -9000.0,
        "inventory": 5200.0,
        "receivables": 9500.0,
        "bse_code": "500010",
    },
    "WIPRO": {
        "revenue": 85000.0,
        "prior_revenue": 79000.0,
        "cogs": 48000.0,
        "operating_profit": 13800.0,
        "ebitda": 15600.0,
        "eps": 9.0,
        "cfo": 12500.0,
        "cfi": -4800.0,
        "cff": -3600.0,
        "inventory": 6100.0,
        "receivables": 8600.0,
        "bse_code": "507685",
    },
}

if "company_input" not in st.session_state:
    st.session_state.company_input = "TCS"
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = st.session_state.company_input
if "search_text" not in st.session_state:
    st.session_state.search_text = ""
if "company_status" not in st.session_state:
    st.session_state.company_status = ""
if "animation_id" not in st.session_state:
    st.session_state.animation_id = 0
if "last_company" not in st.session_state:
    st.session_state.last_company = st.session_state.company_input

manual_defaults = {
    "revenue": 100000.0,
    "prior_revenue": 90000.0,
    "cogs": 60000.0,
    "operating_profit": 17000.0,
    "ebitda": 22000.0,
    "eps": 12.5,
    "cfo": 18000.0,
    "cfi": -5000.0,
    "cff": -2000.0,
    "inventory": 12000.0,
    "receivables": 15000.0,
    "equity_capital": 200.0,
    "dividend_payout": 20.0,
}
for key, value in manual_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

if st.session_state.selected_ticker != st.session_state.company_input:
    st.session_state.company_input = st.session_state.selected_ticker


def select_company(ticker: str):
    ticker = ticker.strip().upper()
    st.session_state.selected_ticker = ticker
    st.session_state.company_input = ticker
    st.session_state.company_status = f"Loaded {ticker}"
    st.session_state.animation_id += 1


def refresh_dashboard():
    st.session_state.selected_ticker = st.session_state.company_input.strip().upper()
    st.session_state.company_status = f"Refreshed {st.session_state.selected_ticker}"
    st.session_state.animation_id += 1


def search_screener_companies(query: str) -> list[str]:
    if not query or len(query.strip()) < 2:
        return []
    try:
        api_url = f"https://www.screener.in/api/company/search/?q={query.strip()}"
        result = requests.get(api_url, timeout=6)
        result.raise_for_status()
        data = result.json()
        return [item.get("symbol") for item in data if item.get("symbol")]
    except Exception:
        return []


def parse_screener_rows(html: str) -> list[list[str]]:
    class ScreenerRowParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_td = False
            self.current = ""
            self.row = []
            self.rows = []

        def handle_starttag(self, tag, attrs):
            if tag == "td":
                self.in_td = True
                self.current = ""

        def handle_endtag(self, tag):
            if tag == "td":
                self.in_td = False
                value = self.current.strip().replace("\xa0", " ")
                self.row.append(value)
            elif tag == "tr":
                if self.row:
                    self.rows.append(self.row)
                self.row = []

        def handle_data(self, data):
            if self.in_td:
                self.current += data

    parser = ScreenerRowParser()
    parser.feed(html)
    return parser.rows


from typing import Dict, List, Optional, Tuple

def parse_number(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    clean = value.replace("₹", "").replace("Cr", "").replace("%", "").replace(",", "").strip()
    if clean in ("", "-", "—"):
        return None
    try:
        return float(clean)
    except ValueError:
        return None


def fetch_screener_company_data(ticker: str) -> Tuple[Dict[str, float], Optional[str]]:
    try:
        url = f"https://www.screener.in/company/{ticker}/consolidated/"
        response = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        rows = parse_screener_rows(response.text)

        data: dict[str, float] = {}
        for row in rows:
            if not row:
                continue
            label = row[0].lower().replace("\xa0", " ").replace("&nbsp;", " ").strip()
            values = [parse_number(col) for col in row[1:]]
            latest = next((v for v in reversed(values) if v is not None), None)
            prior = None
            if latest is not None:
                reversed_values = list(reversed(values))
                remaining = reversed_values[1:]
                prior = next((v for v in remaining if v is not None), None)

            if "sales +" in label:
                if latest is not None:
                    data["revenue"] = latest
                if prior is not None:
                    data["prior_revenue"] = prior
            elif "expenses +" in label:
                if latest is not None:
                    data["expenses"] = latest
            elif label == "operating profit":
                data["operating_profit"] = latest
            elif label == "cash from operating activity +":
                data["cfo"] = latest
            elif label == "cash from investing activity +":
                data["cfi"] = latest
            elif label == "cash from financing activity +":
                data["cff"] = latest
            elif label == "eps in rs":
                data["eps"] = latest
            elif label == "inventory days":
                data["inventory_days"] = latest
            elif label == "debtor days":
                data["receivable_days"] = latest
            elif label == "interest":
                data["interest"] = latest
            elif label == "depreciation":
                data["depreciation"] = latest
            elif label == "equity capital":
                data["equity_capital"] = latest
            elif label == "dividend payout %":
                data["dividend_payout"] = latest

        if "expenses" in data and "revenue" in data and "cogs" not in data:
            data["cogs"] = data["expenses"]
        if "operating_profit" in data and "depreciation" in data and "interest" in data:
            data["ebitda"] = (data.get("operating_profit", 0.0)
                               + data.get("depreciation", 0.0)
                               + data.get("interest", 0.0))

        return data, None
    except Exception as e:
        return {}, str(e)


def parse_live_numeric(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return parse_number(str(value))


def fmt_amount(x):
    if x is None:
        return "N/A"
    try:
        return f"₹{x:,.0f}"
    except Exception:
        return str(x)


def fmt_pct_frac(x):
    if x is None:
        return "N/A"
    try:
        return f"{x:.2%}"
    except Exception:
        return str(x)


def fmt_pct_raw(x):
    if x is None:
        return "N/A"
    try:
        return f"{x:.2f}%"
    except Exception:
        return str(x)


def fmt_number(x, digits: int = 2):
    if x is None:
        return "N/A"
    try:
        return f"{x:.{digits}f}"
    except Exception:
        return str(x)


def normalize_mcp_data(raw_data: dict) -> dict:
    normalized = {}
    mapping = {
        "revenue": ["revenue", "sales", "turnover", "net_sales"],
        "prior_revenue": ["prior_revenue", "previous_revenue", "last_year_revenue"],
        "cogs": ["cogs", "cost_of_goods_sold"],
        "operating_profit": ["operating_profit", "operating_income", "ebit"],
        "ebitda": ["ebitda"],
        "eps": ["eps", "earnings_per_share"],
        "cfo": ["cfo", "cash_flow_operating", "cash_from_operating_activity"],
        "cfi": ["cfi", "cash_flow_investing", "cash_from_investing_activity"],
        "cff": ["cff", "cash_flow_financing", "cash_from_financing_activity"],
        "inventory": ["inventory", "inventory_balance"],
        "receivables": ["receivables", "debtor_days", "debtor_bookings", "receivable_balance"],
        "debt_to_equity": ["debt_to_equity", "debt/equity", "debt to equity", "debt_equity"],
        "dividend_yield": ["dividend_yield", "dividend yield", "dividend_yield_pct", "dividend%"],
        "inventory_days": ["inventory_days"],
        "receivable_days": ["receivable_days", "debtor_days"],
    }
    for normalized_key, raw_keys in mapping.items():
        for raw_key in raw_keys:
            if raw_key in raw_data:
                value = parse_live_numeric(raw_data[raw_key])
                if value is not None:
                    normalized[normalized_key] = value
                    break
    return normalized

with st.sidebar:
    st.header("Company selection")
    selected_company = st.selectbox(
        "Choose a company",
        sample_companies,
        index=sample_companies.index(st.session_state.selected_ticker) if st.session_state.selected_ticker in sample_companies else 0,
    )
    if st.button("Confirm selection"):
        st.session_state.selected_ticker = selected_company
        st.session_state.company_input = selected_company
        st.session_state.company_status = f"Loaded {selected_company}"
        st.session_state.animation_id += 1

    st.caption("Select a company from the list and press Confirm to load details.")

company_name = st.session_state.selected_ticker
live_data = {}
live_source = "Screener.in scrape"
scraped_data = {}
sc_error = None
# Defaults for simplified UI (no MCP/manual controls)
use_mcp = False
use_manual = False
mcp_data = None
if company_name:
    scraped_data, sc_error = fetch_screener_company_data(company_name)
    if scraped_data:
        st.success(f"Loaded live Screener.in data for {company_name}")
        live_data = scraped_data
    else:
        st.error("Live Screener.in data is unavailable for this ticker right now. No fallback data will be used.")

metric_keys = [
    "revenue", "prior_revenue", "cogs", "operating_profit", "ebitda",
    "eps", "cfo", "cfi", "cff", "inventory", "receivables",
    "equity_capital", "dividend_payout",
]
if company_name != st.session_state.last_company:
    st.session_state.last_company = company_name
    if live_data:
        for key in metric_keys:
            if key in live_data:
                st.session_state[key] = live_data[key]
            else:
                st.session_state[key] = None
    else:
        for key in metric_keys:
            st.session_state[key] = None

if not use_mcp and live_data:
    st.sidebar.info("Using live Screener.in scraped values. Enable local MCP to prefer local server data.")

if use_manual:
    with st.sidebar.expander("Manual accounting values", expanded=True):
        st.warning("Manual overrides are disabled for live-only mode. This app will not use any manual or sample values when live Screener data is unavailable.")

        default_revenue = live_data.get("revenue", None)
        default_prior_revenue = live_data.get("prior_revenue", None)
        default_cogs = live_data.get("cogs", None)
        default_operating_profit = live_data.get("operating_profit", None)
        default_ebitda = live_data.get("ebitda", None)
        default_eps = live_data.get("eps", None)
        default_cfo = live_data.get("cfo", None)
        default_cfi = live_data.get("cfi", None)
        default_cff = live_data.get("cff", None)
        default_inventory = live_data.get("inventory", None)
        default_receivables = live_data.get("receivables", None)
        default_equity_capital = live_data.get("equity_capital", None)
        default_dividend_payout = live_data.get("dividend_payout", None)

        revenue = st.number_input("Revenue (Sales) — 1 year", min_value=0.0, value=default_revenue if default_revenue is not None else 0.0, step=1000.0, format="%.2f", key="revenue")
        prior_revenue = st.number_input("Previous period Revenue — 1 year", min_value=0.0, value=default_prior_revenue if default_prior_revenue is not None else 0.0, step=1000.0, format="%.2f", key="prior_revenue")
        cogs = st.number_input("Cost of Goods Sold (COGS) — 1 year", min_value=0.0, value=default_cogs if default_cogs is not None else 0.0, step=1000.0, format="%.2f", key="cogs")
        operating_profit = st.number_input("Operating Profit — 1 year", min_value=0.0, value=default_operating_profit if default_operating_profit is not None else 0.0, step=1000.0, format="%.2f", key="operating_profit")
        ebitda = st.number_input("EBITDA — 1 year", min_value=0.0, value=default_ebitda if default_ebitda is not None else 0.0, step=1000.0, format="%.2f", key="ebitda")
        eps = st.number_input("Earnings Per Share (EPS) — 1 year", min_value=0.0, value=default_eps if default_eps is not None else 0.0, step=0.1, format="%.2f", key="eps")
        st.markdown("---")
        cfo = st.number_input("Cash Flow from Operating Activities (CFO) — 1 year", value=default_cfo if default_cfo is not None else 0.0, step=1000.0, format="%.2f", key="cfo")
        cfi = st.number_input("Cash Flow from Investing Activities (CFI) — 1 year", value=default_cfi if default_cfi is not None else 0.0, step=1000.0, format="%.2f", key="cfi")
        cff = st.number_input("Cash Flow from Financing Activities (CFF) — 1 year", value=default_cff if default_cff is not None else 0.0, step=1000.0, format="%.2f", key="cff")
        st.markdown("---")
        inventory = st.number_input("Inventory — 1 year", min_value=0.0, value=default_inventory if default_inventory is not None else 0.0, step=500.0, format="%.2f", key="inventory")
        receivables = st.number_input("Receivables — 1 year", min_value=0.0, value=default_receivables if default_receivables is not None else 0.0, step=500.0, format="%.2f", key="receivables")
        equity_capital = st.number_input("Equity Capital (₹ Cr)", min_value=0.0, value=default_equity_capital if default_equity_capital is not None else 0.0, step=10.0, format="%.2f", key="equity_capital")
        dividend_payout = st.number_input("Dividend Payout %", min_value=0.0, value=default_dividend_payout if default_dividend_payout is not None else 0.0, step=0.1, format="%.2f", key="dividend_payout")
else:
    revenue = live_data.get("revenue", None)
    prior_revenue = live_data.get("prior_revenue", None)
    cogs = live_data.get("cogs", None)
    operating_profit = live_data.get("operating_profit", None)
    ebitda = live_data.get("ebitda", None)
    eps = live_data.get("eps", None)
    cfo = live_data.get("cfo", None)
    cfi = live_data.get("cfi", None)
    cff = live_data.get("cff", None)
    inventory = live_data.get("inventory", None)
    receivables = live_data.get("receivables", None)
    equity_capital = live_data.get("equity_capital", None)
    dividend_payout = live_data.get("dividend_payout", None)

    inventory_value = live_data.get("inventory")
    if inventory_value is not None:
        inventory = inventory_value
    elif "inventory_days" in live_data and cogs is not None and live_data.get("inventory_days") is not None:
        inventory = cogs * live_data["inventory_days"] / 365.0
    else:
        inventory = None

    receivables_value = live_data.get("receivables")
    if receivables_value is not None:
        receivables = receivables_value
    elif "receivable_days" in live_data and revenue is not None and live_data.get("receivable_days") is not None:
        receivables = revenue * live_data["receivable_days"] / 365.0
    else:
        receivables = None

if live_data:
    if live_source == "MCP":
        st.markdown("## Live Screener.in MCP data")
        st.write("The following data is fetched from your local MCP server.")
        st.json(mcp_data)
    else:
        st.info(f"Using live {live_source} values for dashboard metrics.")
elif use_mcp:
    st.error("Live MCP data is unavailable. The dashboard is currently displaying sample/manual values only.")
else:
    st.info("Local MCP is not enabled. The dashboard is displaying sample/manual values only.")

company_class = "company-display animate" if st.session_state.animation_id else "company-display"
company_status = st.session_state.company_status
status_markup = f'<span class="company-badge">{company_status}</span>' if company_status else ""
company_bse = sample_company_data.get(company_name, {}).get("bse_code")
company_label = company_name
if company_bse:
    company_label = f"{company_name} (BSE: {company_bse})"

st.markdown(
    f'<div class="card" style="display:flex;align-items:center;justify-content:space-between;gap:1rem;margin-bottom:1rem"><div style="font-weight:700">Selected company: <span style="color:#0f62fe">{company_label}</span></div><div>{status_markup}</div></div>',
    unsafe_allow_html=True,
)

sales_growth = ((revenue - prior_revenue) / prior_revenue) if (revenue is not None and prior_revenue not in (None, 0)) else 0.0
opm = (operating_profit / revenue) if (operating_profit is not None and revenue not in (None, 0)) else 0.0
gross_profit = (revenue - cogs) if (revenue is not None and cogs is not None) else None
gross_profit_margin = (gross_profit / revenue) if (gross_profit is not None and revenue not in (None, 0)) else 0.0
inventory_days = (inventory / cogs * 365) if (inventory is not None and cogs not in (None, 0)) else 0.0
receivable_turnover = (revenue / receivables) if (revenue is not None and receivables not in (None, 0)) else 0.0
receivable_days = (365 / receivable_turnover) if (receivable_turnover not in (None, 0)) else 0.0

bse_code = sample_company_data.get(company_name, {}).get("bse_code", "N/A")

summary = {
    "Company": company_name,
    "BSE Code": bse_code,
    "Revenue": fmt_amount(revenue),
    "Sales Growth": fmt_pct_frac(sales_growth),
    "Operating Profit": fmt_amount(operating_profit),
    "OPM": fmt_pct_frac(opm),
    "EBITDA": fmt_amount(ebitda),
    "EPS": fmt_number(eps, 2),
    "CFO": fmt_amount(cfo),
    "CFI": fmt_amount(cfi),
    "CFF": fmt_amount(cff),
    "Gross Profit": fmt_amount(gross_profit),
    "Gross Margin": fmt_pct_frac(gross_profit_margin),
    "Equity Capital": fmt_amount(equity_capital),
    "Dividend Payout": fmt_pct_raw(dividend_payout),
    "Inventory Days": fmt_number(inventory_days, 1),
    "Receivable Turnover": fmt_number(receivable_turnover, 2),
    "Receivable Days": fmt_number(receivable_days, 1),
}

st.markdown('<div class="section-header">Dashboard overview</div>', unsafe_allow_html=True)
with st.container():
    cols = st.columns([1.2,1,1,1])
    with cols[0]:
        st.markdown('<div class="card metrics-row">', unsafe_allow_html=True)
        st.metric("Revenue (₹ Cr)", fmt_amount(revenue))
        st.markdown('</div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown('<div class="card metrics-row">', unsafe_allow_html=True)
        st.metric("Sales Growth", fmt_pct_frac(sales_growth))
        st.metric("Operating Profit", fmt_amount(operating_profit))
        st.markdown('</div>', unsafe_allow_html=True)
    with cols[2]:
        st.markdown('<div class="card metrics-row">', unsafe_allow_html=True)
        st.metric("EBITDA", fmt_amount(ebitda))
        st.metric("EPS", fmt_number(eps,2))
        st.markdown('</div>', unsafe_allow_html=True)
    with cols[3]:
        st.markdown('<div class="card metrics-row">', unsafe_allow_html=True)
        st.metric("CFO", fmt_amount(cfo))
        st.metric("Gross Margin", fmt_pct_frac(gross_profit_margin))
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-header">Cash flow & working capital</div>', unsafe_allow_html=True)
flow_df = pd.DataFrame(
    {
        "Metric": ["CFO", "CFI", "CFF"],
        "Amount": [cfo, cfi, cff],
    }
)
try:
    st.bar_chart(flow_df.set_index("Metric")["Amount"])
except Exception:
    st.dataframe(flow_df, use_container_width=True, hide_index=True)

st.markdown('<div class="section-header">KPI summary</div>', unsafe_allow_html=True)
metric_df = pd.DataFrame([summary]).T.rename(columns={0: "Value"})
metric_df["Value"] = metric_df["Value"].astype(str)
st.table(metric_df)

score = 0
score += 1 if sales_growth >= 0.1 else 0
score += 1 if opm >= 0.15 else 0
score += 1 if gross_profit_margin >= 0.25 else 0
score += 1 if cfo > 0 else 0
score += 1 if receivable_days <= 90 else 0

if score >= 4:
    judgment = "Strong investment signal"
elif score == 3:
    judgment = "Good investment signal"
elif score == 2:
    judgment = "Caution: review further"
else:
    judgment = "Weak signal: needs more analysis"

st.markdown('<div class="section-header">Investment guidance</div>', unsafe_allow_html=True)
indicator = "✅" if score >= 3 else "⚠️"
st.markdown(f"### {indicator} {judgment}")
st.write(
    "This signal is based on growth, margin, cash flow, and receivable efficiency. "
    "Use it as a directional check, and combine with business quality and strategy analysis."
)

with st.expander("How the signal is generated"):
    st.markdown(
        "- Sales Growth: target at least 10%.\n"
        "- Operating Profit Margin: target at least 15%.\n"
        "- Gross Profit Margin: target at least 25%.\n"
        "- Cash Flow from operations should be positive.\n"
        "- Receivable Days should be 90 or lower."
    )

# Generate human-readable reasons and risks for the investment signal
reasons = []
risks = []

if sales_growth >= 0.10:
    reasons.append(f"Revenue growth of {sales_growth:.1%} — top-line is expanding.")
else:
    risks.append(f"Sales growth is low ({sales_growth:.1%}) compared with the 10% target.")

if opm >= 0.15:
    reasons.append(f"Operating Profit Margin {opm:.1%} — business converts sales to profit effectively.")
else:
    risks.append(f"Operating margin is modest ({opm:.1%}), check cost structure.")

if gross_profit_margin >= 0.25:
    reasons.append(f"Gross Margin {gross_profit_margin:.1%} — good product/service pricing or low direct costs.")
else:
    risks.append(f"Gross margin is below target ({gross_profit_margin:.1%}), investigate unit economics.")

if cfo and cfo > 0:
    reasons.append(f"Positive CFO of {fmt_amount(cfo)} (₹ Crore-scale) — operations generate cash.")
else:
    risks.append(f"Cash flow from operations is negative or weak (CFO = {fmt_amount(cfo)}), watch liquidity.")

if receivable_days <= 90:
    reasons.append(f"Receivable days {receivable_days:.0f} — healthy working capital cycle.")
else:
    risks.append(f"Receivable days high ({receivable_days:.0f}), potential collection or credit issues.")

if dividend_payout and dividend_payout > 0:
    reasons.append(f"Dividend payout {fmt_pct_raw(dividend_payout)} — returns cash to shareholders.")

if equity_capital:
    reasons.append(f"Equity capital ~{fmt_amount(equity_capital)} Cr — balance sheet scale to absorb volatility.")

if not reasons:
    reasons.append("No strong positive signals detected from the selected KPIs.")

st.markdown('<div class="section-header">Why this signal (reasons & risks)</div>', unsafe_allow_html=True)
cols = st.columns(2)
with cols[0]:
    st.markdown("**Reasons to consider this company**")
    st.markdown("\n".join([f"- {r}" for r in reasons]))
with cols[1]:
    st.markdown("**Risks and cautionary points**")
    if risks:
        st.markdown("\n".join([f"- {r}" for r in risks]))
    else:
        st.markdown("- No immediate red flags from the selected KPIs.")

if mcp_data:
    st.markdown('<div class="section-header">Screener.in live MCP insights</div>', unsafe_allow_html=True)
    if "market_cap" in mcp_data:
        st.metric("Market Cap", f"₹{mcp_data.get('market_cap'):,.0f}")
    if "profit" in mcp_data:
        st.metric("Profit", f"₹{mcp_data.get('profit'):,.0f}")
    if "mcp_ratio" in mcp_data:
        st.metric("MCP Ratio", f"{mcp_data.get('mcp_ratio')}x")

st.markdown("---")
st.caption(
    "Enter any Screener.in ticker and use the local MCP server to load live data. "
    "If you do not have an MCP server running, use manual inputs for quick analysis. "
    "Rupee amounts from Screener are interpreted as ₹ Crore values unless otherwise noted."
)
st.markdown('<div class="section-header">Example companies to avoid</div>', unsafe_allow_html=True)
st.write(
    "These tickers are shown as illustrative examples of weaker investment candidates based on a simple cash-flow and receivable signal. "
    "Always do your own research before acting."
)
st.write(', '.join(avoid_companies))

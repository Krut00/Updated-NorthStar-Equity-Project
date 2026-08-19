# NorthStar Equity Handoff

Read this file before making any changes. Continue implementation autonomously; do not ask the user to repeat requirements.

## Project

NorthStar Equity is a premium financial-analysis dashboard. It fetches live company data from Screener, analyzes the selected metrics, compares the company with its sector, explains strengths and risks, and generates an academic equity analyst report.

Project directory:

`/Users/krut/finance-dashboard`

Important files:

- `index.html`: dashboard frontend
- `server.py`: Screener proxy and Gemini report backend
- `North_Star_Freedom_Logo.svg`: only permitted NorthStar header logo
- `iim-ranchi-logo.png`: use only in the final academic disclaimer
- `northstar-equity-analyst-report.txt`: text report reference

## Brand

Name: **NorthStar Equity**

Motto, on two lines:

```text
Find the Signal
Inside the Noise
```

Use only `North_Star_Freedom_Logo.svg` beside NorthStar Equity.

Do not put the IIM Ranchi logo beside NorthStar Equity. Use it only in the disclaimer at the very end.

## Live Server

Use port `8005`. Do not use stale port `8003`.

Start from any directory with:

```bash
cd /Users/krut/finance-dashboard
PORT=8005 python3 /Users/krut/finance-dashboard/server.py
```

`server.py` changes into its own project directory automatically.

Required endpoints:

- `GET /api/company?symbol=TCS`
- `GET /api/search?q=tcs`
- `GET /api/health`
- `POST /api/generate-report`

The backend must read the Gemini key only from `GEMINI_API_KEY`. Never ask the user for a key in chat, never print it, and never place it in frontend JavaScript.

## Current Live Data Requirements

Use current Screener data only. Never use demo or dummy fallback values.

For every selected company, fetch and display when available:

- Company name
- Symbol
- Current market price
- Daily movement
- Quote date
- Market capitalization
- P/E
- ROCE
- ROE
- Revenue growth
- Operating margin
- Debt/equity
- Revenue historical series
- Operating profit / EBITDA proxy historical series
- Operating cash-flow historical series
- Debtor days
- Inventory days
- Days payable
- Cash conversion cycle
- Actual Screener fiscal period labels
- Actual Screener sector classification
- Same-sector peer data

If a field is not available, show:

`Unavailable from current Screener response.`

Never invent data, reuse stale data, or show demo data. Volume has been removed and must remain removed. Do not display the phrase `Not provided by Screener page`.

The page must show loading state and successful fetch timestamp. On fetch failure, clear current data and do not leave the previous company visible.

## Dashboard Sections

The dashboard must include:

1. Company header and search/type-ahead company selector
2. Live Screener status and timestamp
3. Company snapshot
4. CCC chart with clear axes, live fiscal labels, exact hover details, and readable bars
5. Financial snapshot with revenue growth, operating margin, ROE, debt/equity, current price, market cap, P/E, and ROCE
6. Three historical financial charts:
   - Revenue
   - Operating profit / EBITDA proxy
   - Operating cash flow
7. Working-capital section:
   - Debtor days
   - Inventory days
   - Days payable
   - Cash conversion cycle
8. Company-versus-sector comparison for:
   - Revenue growth
   - Operating margin
   - ROE
   - Debt/equity
9. One neutral peer section titled:
   `Companies in the same sector`
10. Clickable live peer cards
11. Reasons to consider the company
12. Warnings and risks
13. Detailed investor interpretation
14. Downloadable equity analyst report
15. Gemini AI report generation
16. Score methodology only if requested. The visible score was requested to be removed from the website; do not show a visible score card unless the user explicitly asks to restore it.
17. Final disclaimer at the end of the page, immediately before the footer

## Peer Rules

Internally try to select five valid same-sector companies:

- two stronger
- one similar scale
- two lower scale

Do not display those category names. Only show the neutral heading `Companies in the same sector`.

Do not invent peers. If fewer valid live peers exist, show only those and explain that fewer peers were available.

Clicking a peer must fetch and replace all company data, charts, comparisons, interpretation, and report data.

## Gemini AI Report

The dashboard has a `Generate AI analyst report` button.

The backend must call Gemini `generateContent` using `GEMINI_API_KEY`. The report must be generated only from the current live Screener response and include:

- Executive investment view
- Company snapshot
- Financial snapshot
- Revenue, operating-profit/EBITDA, and cash-flow history
- Working-capital analysis
- CCC analysis
- Sector comparison
- Peer companies
- Reasons to consider
- Warnings and risks
- Detailed recommendation
- Missing-data disclosure
- Screener source URL
- Fetch timestamp
- IIM Ranchi academic disclaimer

Never invent values or facts. Missing data must be explicitly disclosed.

## Disclaimer

The final page section must state:

```text
This is an academic project by IIM Ranchi. Kindly do not use it to make financial or investment decisions. This dashboard is not investment advice.
```

Keep the IIM Ranchi logo in this final section only.

## Three Prompt Names

### Prompt Live Data

Use live Screener data only. Validate the response schema, match company identity and source URL, preserve actual fiscal labels, clear stale data before loading a new company, show loading and fetch timestamp, never invent missing values, never show demo data, and fail clearly when Screener is unavailable. Test TCS, Infosys, Hindustan Unilever, and a company from another sector.

### Everything Displayed

Audit that every requested metric, chart, working-capital field, sector comparison, peer card, recommendation, AI report field, timestamp, source URL, and disclaimer is visibly rendered from the current live response. Ensure chart labels and tooltips are readable, no values collide, no stale company text remains, and the report matches the dashboard.

### Element Check

Use a real browser at 1440x900, 1280x800, 1024x768, 768x1024, 390x844, and 375x667. Check no overlap, clipping, horizontal overflow, chart overflow, tooltip clipping, hidden controls, peer-card problems, stale loading states, missing DOM fields, logo problems, disclaimer placement, and browser console errors. Compare API values with visible DOM values.

## Validation Before Completion

Run:

```bash
python3 -m py_compile /Users/krut/finance-dashboard/server.py
```

Check editor diagnostics for `index.html` and `server.py`.

Check:

```bash
curl http://localhost:8005/api/health
curl 'http://localhost:8005/api/company?symbol=TCS'
curl 'http://localhost:8005/api/company?symbol=INFY'
curl 'http://localhost:8005/api/search?q=tcs'
```

Test the AI endpoint with POST after Gemini is configured:

```bash
curl -X POST http://localhost:8005/api/generate-report \
  -H 'Content-Type: application/json' \
  -d '{"company":"TCS"}'
```

Do not claim completion without fresh browser validation.

## New Chat Instruction

In a new chat, paste only this:

```text
Read /Users/krut/finance-dashboard/NORTHSTAR_HANDOFF.md completely. Continue the NorthStar Equity project autonomously. Inspect the current files, run the three prompts named Prompt Live Data, Everything Displayed, and Element Check, fix all issues you find, and validate the live website on port 8005. Do not ask me to repeat requirements or share secrets.
```

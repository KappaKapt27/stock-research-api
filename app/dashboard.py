from __future__ import annotations

from fastapi import HTTPException
from fastapi.responses import HTMLResponse


def build_dashboard_html() -> HTMLResponse:
    html = """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Research Stock Dashboard</title>
        <style>
          body { font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 2rem; }
          h1 { margin-bottom: 0.5rem; }
          .card { background: #111827; border: 1px solid #334155; border-radius: 12px; padding: 1rem; margin-top: 1rem; }
          .row { display: flex; gap: 1rem; flex-wrap: wrap; }
          .chip { background: #1e293b; border: 1px solid #475569; padding: 0.35rem 0.7rem; border-radius: 999px; }
          input, button { padding: 0.7rem 1rem; border-radius: 8px; border: 1px solid #475569; }
          input { width: 200px; background: #020817; color: white; }
          button { background: #2563eb; color: white; cursor: pointer; }
          table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
          th, td { border-bottom: 1px solid #334155; padding: 0.75rem; text-align: left; }
          .muted { color: #94a3b8; }
        </style>
      </head>
      <body>
        <h1>Research Stock Dashboard</h1>
        <p class="muted">This dashboard is for research and educational review only. It does not place orders or execute trades.</p>

        <div class="card">
          <div class="row">
            <input id="symbolInput" value="AAPL" />
            <button onclick="loadQuote()">Load Symbol</button>
            <button onclick="loadWatchlist()">Load Watchlist</button>
          </div>
        </div>

        <div class="card">
          <div id="quoteResult">Loading...</div>
        </div>

        <div class="card">
          <h3>Watchlist</h3>
          <table>
            <thead>
              <tr><th>Symbol</th><th>Price</th><th>Change</th><th>Source</th></tr>
            </thead>
            <tbody id="watchlistTable"></tbody>
          </table>
        </div>

        <script>
          async function api(path) {
            const res = await fetch(path);
            if (!res.ok) throw new Error('Request failed');
            return res.json();
          }

          async function loadQuote() {
            const symbol = document.getElementById('symbolInput').value.trim();
            const quote = await api(`/quote/${symbol}`);
            document.getElementById('quoteResult').innerHTML = `
              <div class='row'>
                <span class='chip'>Symbol: ${quote.symbol}</span>
                <span class='chip'>Price: $${quote.price}</span>
                <span class='chip'>Change: ${quote.change ?? 0}</span>
                <span class='chip'>Source: ${quote.source}</span>
              </div>
              <p class='muted'>${quote.research_note}</p>
            `;
          }

          async function loadWatchlist() {
            const symbols = 'AAPL,MSFT,NVDA,AMZN,GOOGL';
            const data = await api(`/watchlist?symbols=${encodeURIComponent(symbols)}`);
            const rows = data.data.map(item => `
              <tr>
                <td>${item.symbol}</td>
                <td>$${item.price}</td>
                <td>${item.change ?? 0}</td>
                <td>${item.source}</td>
              </tr>
            `).join('');
            document.getElementById('watchlistTable').innerHTML = rows;
          }

          loadWatchlist();
          loadQuote();
        </script>
      </body>
    </html>
    """
    return HTMLResponse(html)

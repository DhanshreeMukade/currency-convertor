from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

# ---------- Inline HTML + CSS + JS (no separate files needed) ----------
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Currency Converter</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: radial-gradient(1200px circle at 10% 10%, #b2f1ff 0, transparent 40%),
                  radial-gradient(1200px circle at 90% 20%, #ffd7f0 0, transparent 40%),
                  linear-gradient(135deg, #74ebd5, #acb6e5);
    }
    .card {
      width: min(92vw, 420px);
      background: #fff;
      padding: 28px 24px;
      border-radius: 18px;
      box-shadow: 0 18px 45px rgba(0,0,0,.15);
      border: 1px solid rgba(0,0,0,.06);
    }
    .title {
      display: flex; align-items: center; gap: 10px;
      font-weight: 800; font-size: 22px; color: #111;
      margin-bottom: 14px;
    }
    .subtitle { color: #666; font-size: 13px; margin-bottom: 18px; }
    .row { display: flex; gap: 12px; }
    .row > * { flex: 1; }
    input, select, button {
      width: 100%;
      padding: 12px 14px;
      border-radius: 10px;
      border: 1px solid #d7dce1;
      font-size: 15px;
      outline: none;
      transition: .2s border, .2s box-shadow, .2s transform;
      background: #fff;
    }
    input:focus, select:focus {
      border-color: #63b3ed;
      box-shadow: 0 0 0 4px rgba(99,179,237,.15);
    }
    button {
      background: linear-gradient(135deg, #4facfe, #00f2fe);
      color: #fff; font-weight: 700; border: none; cursor: pointer; margin-top: 8px;
    }
    button:hover { transform: translateY(-1px); }
    button:disabled { opacity: .7; cursor: not-allowed; }
    .result {
      margin-top: 14px; font-size: 16px; font-weight: 700; color: #111;
      min-height: 22px;
    }
    .error { color: #b00020; font-weight: 600; }
    .muted { color: #667; font-size: 12px; margin-top: 6px; }
  </style>
</head>
<body>
  <div class="card">
    <div class="title">💱 Currency Converter</div>
    <div class="subtitle">Live rates via Frankfurter (no API key needed)</div>

    <label>Amount</label>
    <input type="number" id="amount" placeholder="Enter amount" min="0" step="any"/>

    <div class="row" style="margin-top:12px">
      <div>
        <label>From</label>
        <select id="from">
          <option>USD</option>
          <option>EUR</option>
          <option>INR</option>
          <option>GBP</option>
          <option>JPY</option>
          <option>AUD</option>
          <option>CAD</option>
          <option>CHF</option>
          <option>CNY</option>
          <option>SGD</option>
        </select>
      </div>
      <div>
        <label>To</label>
        <select id="to">
          <option>INR</option>
          <option>USD</option>
          <option>EUR</option>
          <option>GBP</option>
          <option>JPY</option>
          <option>AUD</option>
          <option>CAD</option>
          <option>CHF</option>
          <option>CNY</option>
          <option>SGD</option>
        </select>
      </div>
    </div>

    <button id="btn">Convert</button>
    <div id="result" class="result"></div>
    <div class="muted">Tip: same currency → same amount</div>
  </div>

  <script>
    const btn = document.getElementById('btn');
    async function convert() {
      const amount = document.getElementById('amount').value.trim();
      const from = document.getElementById('from').value;
      const to = document.getElementById('to').value;
      const out = document.getElementById('result');

      if (!amount) { out.innerHTML = '<span class="error">Please enter an amount.</span>'; return; }

      btn.disabled = true; out.textContent = 'Converting...';
      try {
        const res = await fetch('/convert', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ amount, from, to })
        });
        const data = await res.json();
        if (data.error) out.innerHTML = '<span class="error">'+data.error+'</span>';
        else out.textContent = `${amount} ${from} = ${data.result} ${to}`;
      } catch (e) {
        out.innerHTML = '<span class="error">Network error.</span>';
      } finally {
        btn.disabled = false;
      }
    }
    btn.addEventListener('click', convert);
    // Enter key to convert
    document.getElementById('amount').addEventListener('keydown', e => { if (e.key==='Enter') convert(); });
  </script>
</body>
</html>
"""

# ------------------------ Routes ------------------------

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

@app.route("/convert", methods=["POST"])
def convert():
    try:
        data = request.get_json(force=True)
        amount = float(data.get("amount", 0))
        from_currency = (data.get("from") or "").upper()
        to_currency = (data.get("to") or "").upper()

        if amount < 0:
            return jsonify(error="Amount cannot be negative.")
        if not from_currency or not to_currency:
            return jsonify(error="Choose both currencies.")
        if from_currency == to_currency:
            return jsonify(result=round(amount, 2))

        # Frankfurter public API (no key needed)
        # Example: https://api.frankfurter.app/latest?amount=10&from=USD&to=INR
        resp = requests.get(
            "https://api.frankfurter.app/latest",
            params={"amount": amount, "from": from_currency, "to": to_currency},
            timeout=10,
        )
        if resp.status_code != 200:
            return jsonify(error="Rates source not available right now.")
        payload = resp.json()
        rates = payload.get("rates", {})
        if to_currency not in rates:
            return jsonify(error="Currency not supported.")
        converted = float(rates[to_currency])
        return jsonify(result=round(converted, 2))
    except Exception as e:
        return jsonify(error=str(e))

if __name__ == "__main__":
    # Install dependencies first:  pip install flask requests
    app.run(debug=True)

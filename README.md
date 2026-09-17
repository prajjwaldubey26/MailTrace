# SIH26106 MailTrace

AI-assisted **email threat detection + Received-chain geolocation + forensic PDF** for the AICTE Cyber Security Cell problem statement.

This prototype analyses **mail you paste or upload**. It does not send mail, does not break into mailboxes, and does **not** name a person from an IP.

## Run

```powershell
cd C:\Users\prajj\Documents\proto.SIH
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000

## Deploy (Render)

This repo is wired for a Python web service:

- Build: `pip install -r requirements.txt`
- Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`

Push to `main` on GitHub. If the existing Render service has auto-deploy on, it rebuilds itself. Otherwise: Render Dashboard → New Web Service → connect `prajjwaldubey26/MailTrace` → those two commands.

Open the `onrender.com` URL after the deploy turns green. There are no env vars to set.

## Jury samples

1. `01_legitimate_college` — SPF/DKIM/DMARC pass, campus path  
2. `02_phishing_invoice` — lookalike PayPal, Tor-tagged origin, raw-IP link  
3. `03_bec_dean` — gift-card BEC, Reply-To mismatch  
4. `04_legitimate_google` — Google security alert (pass)

## Honest limits

- Geolocation uses a **demo IP table** plus optional `ip-api.com` for unknown public IPs.  
- Attribution is **sending infrastructure**, not identity.  
- NLP is rule/cue based (fast, explainable). Swap in a classifier later if needed.

## Contributors

- **prajjwaldubey** ([@prajjwaldubey26](https://github.com/prajjwaldubey26))


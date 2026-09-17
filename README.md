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

## Jury samples

1. `01_legitimate_college` — SPF/DKIM/DMARC pass, campus path  
2. `02_phishing_invoice` — lookalike PayPal, Tor-tagged origin, raw-IP link  
3. `03_bec_dean` — gift-card BEC, Reply-To mismatch  
4. `04_legitimate_google` — Google security alert (pass)

## Honest limits

- Geolocation uses a **demo IP table** plus optional `ip-api.com` for unknown public IPs.  
- Attribution is **sending infrastructure**, not identity.  
- NLP is rule/cue based (fast, explainable). Swap in a classifier later if needed.

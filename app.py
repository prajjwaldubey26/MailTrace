from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from engine.pipeline import analyze_raw
from engine.report import build_pdf
from engine.store import correlate, dashboard, get_case, list_campaigns, list_cases, save_case

ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT / "data" / "samples"

app = FastAPI(title="SIH26106 MailTrace", version="1.0.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return (ROOT / "static" / "index.html").read_text(encoding="utf-8")


@app.get("/favicon.ico")
def favicon() -> FileResponse:
    return FileResponse(
        ROOT / "static" / "favicon.ico",
        media_type="image/x-icon",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "ps": "SIH26106",
        "service": "MailTrace",
        "engine": "weighted_heuristics",
        "ai_claim": "explainable rules — not a neural net",
    }


def _attach_intel(result: dict) -> dict:
    attr = result.get("attribution") or {}
    result["intel"] = correlate(
        result.get("from_addr") or "",
        result.get("from_domain") or "",
        attr.get("origin_ip"),
        exclude_id=result.get("id"),
    )
    return result


SAMPLE_GUIDE = {
    "01_legitimate_college": {
        "title": "Safe college mail",
        "expect": "Should look safe",
        "blurb": "Exam timetable from the college. Sender checks should pass.",
        "tone": "safe",
    },
    "02_phishing_invoice": {
        "title": "Scam invoice",
        "expect": "Should look dangerous",
        "blurb": "Fake PayPal bill. Do not pay. Map shows odd servers.",
        "tone": "danger",
    },
    "03_bec_dean": {
        "title": "Fake dean mail",
        "expect": "Should look dangerous",
        "blurb": "Someone pretending to be the Dean asking for gift cards.",
        "tone": "danger",
    },
    "04_legitimate_google": {
        "title": "Safe Google alert",
        "expect": "Should look safe",
        "blurb": "Normal Google sign-in notice. Sender checks should pass.",
        "tone": "safe",
    },
}


@app.get("/api/samples")
def samples() -> list[dict]:
    out = []
    for p in sorted(SAMPLES.glob("*.eml")):
        meta = SAMPLE_GUIDE.get(
            p.stem,
            {
                "title": p.stem.replace("_", " "),
                "expect": "Click to analyze",
                "blurb": p.name,
                "tone": "neutral",
            },
        )
        out.append({"id": p.stem, "name": p.name, **meta})
    return out


@app.post("/api/analyze")
async def analyze(file: UploadFile | None = File(None), raw: str | None = Form(None), sample_id: str | None = Form(None)):
    name = "paste"
    text = (raw or "").strip()
    if sample_id:
        path = SAMPLES / f"{sample_id}.eml"
        if not path.exists():
            path = SAMPLES / sample_id
        if not path.exists():
            return JSONResponse({"error": "unknown sample"}, status_code=404)
        text = path.read_text(encoding="utf-8", errors="replace")
        name = path.name
    elif file is not None:
        blob = await file.read()
        text = blob.decode("utf-8", errors="replace")
        name = file.filename or "upload.eml"
    if not text:
        return JSONResponse({"error": "empty email"}, status_code=400)
    result = analyze_raw(text, source_name=name)
    cid = save_case(result)
    result["id"] = cid
    return _attach_intel(result)


@app.get("/api/cases")
def cases() -> list[dict]:
    return list_cases()


@app.get("/api/campaigns")
def campaigns() -> list[dict]:
    return list_campaigns()


@app.get("/api/dashboard")
def dash() -> dict:
    return dashboard()


@app.get("/api/cases/{cid}")
def case_one(cid: int):
    data = get_case(cid)
    if not data:
        return JSONResponse({"error": "not found"}, status_code=404)
    return _attach_intel(data)


@app.get("/api/cases/{cid}/report.pdf")
def case_pdf(cid: int):
    data = get_case(cid)
    if not data:
        return JSONResponse({"error": "not found"}, status_code=404)
    pdf = build_pdf(data)
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="sih26106-case-{cid}.pdf"'})

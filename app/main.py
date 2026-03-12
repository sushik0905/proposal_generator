from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import os
import re
import tempfile
from html import escape
from typing import Any, Optional

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

from app.schemas import ProposalRequest
from app.prompt_builder import build_prompt
from app.generator import generate_proposal
from app.cost_logic import calculate_cost


# =====================================
# FASTAPI APP
# =====================================
app = FastAPI(title="AI Proposal Generator")


# =====================================
# CORS CONFIG
# =====================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================
# STATIC FRONTEND SETUP
# =====================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")


# =====================================
# SIMPLE IN-MEMORY STORAGE
# =====================================
LAST_PROPOSAL_HTML: Optional[str] = None
LAST_COST: Optional[str] = None
LAST_PROPOSAL_TEXT: Optional[str] = None


# =====================================
# HELPERS
# =====================================
def extract_proposal_html(result: Any) -> str:
    """
    Makes the app work even if generator returns:
      - plain string
      - dict with different keys
      - None
    """
    if result is None:
        return ""

    if isinstance(result, str):
        return result.strip()

    if isinstance(result, dict):
        for key in [
            "proposal_html",
            "html",
            "proposal",
            "result",
            "text",
            "content",
            "message",
            "final",
            "output",
            "executive_summary",
            "response",
        ]:
            value = result.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        joined = "\n\n".join(
            str(v).strip()
            for v in result.values()
            if isinstance(v, str) and str(v).strip()
        )
        return joined.strip()

    return str(result).strip()


def strip_html(html_text: str) -> str:
    if not html_text:
        return ""
    return re.sub(r"<.*?>", "", html_text)


def normalize_cost(cost: Any) -> str:
    """
    Converts any cost format into readable text.
    Works for string, dict, int, float.
    """
    if cost is None:
        return "Not available"

    if isinstance(cost, dict):
        lines = []
        for key, value in cost.items():
            label = str(key).replace("_", " ").title()
            lines.append(f"{label}: {value}")
        return "\n".join(lines)

    if isinstance(cost, (int, float)):
        return str(cost)

    return str(cost)


def is_generator_error(text: str) -> bool:
    """
    Detects if returned text is actually an error.
    """
    if not text:
        return False

    lowered = text.lower().strip()
    error_patterns = [
        "error connecting to ollama",
        "ollama http error",
        "generator failed",
        "could not connect to ollama",
        "connection refused",
        "not found for url",
        "read timed out",
        "timed out",
        "unexpected ollama response",
        "internal server error",
        "failed to generate",
    ]

    return any(pattern in lowered for pattern in error_patterns)


def text_to_safe_html(text: str) -> str:
    """
    Converts plain text into safe HTML for browser display.
    """
    if not text:
        return ""
    return "<br>".join(escape(text).splitlines())


def build_html(proposal_html: str, cost: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>AI Generated Proposal</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #fff7f1;
                margin: 40px;
                color: #402b2b;
            }}

            .container {{
                background: white;
                padding: 30px;
                border-radius: 18px;
                box-shadow: 0 10px 35px rgba(0,0,0,0.08);
                max-width: 900px;
                margin: auto;
            }}

            h1 {{
                color: #ff5e78;
            }}

            .proposal-box {{
                margin-top: 20px;
                line-height: 1.8;
                white-space: normal;
            }}

            .btn {{
                display: inline-block;
                padding: 12px 20px;
                background: linear-gradient(135deg, #ff7a59, #ff4fa3);
                color: white !important;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                margin-top: 20px;
                margin-right: 10px;
                font-size: 15px;
                font-weight: bold;
                text-decoration: none;
            }}

            .cost {{
                margin-top: 30px;
                padding: 15px;
                background: #fff0f5;
                border-radius: 12px;
                white-space: pre-line;
            }}

            .error {{
                margin-top: 20px;
                padding: 12px;
                background: #fee2e2;
                border-radius: 8px;
                color: #991b1b;
            }}

            .nav {{
                margin-top: 25px;
            }}
        </style>
    </head>

    <body>
        <div class="container">
            <h1>🚀 AI Generated Proposal</h1>

            <div class="proposal-box">
                {proposal_html if proposal_html else '<div class="error"><b>No proposal generated.</b></div>'}
            </div>

            <div class="cost">
                <h3>Estimated Cost</h3>
                <p><b>{escape(cost)}</b></p>
            </div>

            <div class="nav">
                <a href="/frontend/index.html" class="btn">Go To Frontend</a>
                <a href="/download-proposal" class="btn">Download Proposal PDF</a>
            </div>
        </div>
    </body>
    </html>
    """


def build_pdf(proposal_text: str, cost: str) -> str:
    clean_text = strip_html(proposal_text)
    cost_text = normalize_cost(cost)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    doc = SimpleDocTemplate(temp_file.name, pagesize=A4)
    styles = getSampleStyleSheet()

    story = []
    story.append(Paragraph("PROJECT PROPOSAL", styles["Title"]))
    story.append(Spacer(1, 20))

    safe_clean_text = escape(clean_text).replace("\n", "<br/>")
    story.append(Paragraph(safe_clean_text, styles["Normal"]))
    story.append(Spacer(1, 20))

    story.append(Paragraph("Estimated Cost", styles["Heading2"]))
    story.append(Paragraph(escape(cost_text).replace("\n", "<br/>"), styles["Normal"]))

    doc.build(story)

    return temp_file.name


# =====================================
# ROOT ROUTE
# =====================================
@app.get("/", include_in_schema=False)
async def root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return RedirectResponse(url="/frontend/index.html")

    return JSONResponse(
        content={
            "message": "AI Proposal Generator API is running",
            "docs": "/docs",
            "frontend": "/frontend/index.html (if frontend folder exists)"
        }
    )


# =====================================
# BROWSER DEMO GENERATE PAGE
# =====================================
@app.get("/generate-proposal", response_class=HTMLResponse)
async def generate_get():
    global LAST_PROPOSAL_HTML, LAST_COST, LAST_PROPOSAL_TEXT

    sample = ProposalRequest(
        project_title="AI Healthcare Platform",
        industry="Healthcare",
        duration_months=6,
        expected_users=5000,
        tech_stack=["Python", "FastAPI"]
    )

    try:
        prompt = build_prompt(sample)
        result = generate_proposal(prompt)
        proposal_text = extract_proposal_html(result)

        if not proposal_text:
            proposal_text = "No proposal generated. Generator returned empty output."

        if is_generator_error(proposal_text):
            raise HTTPException(status_code=500, detail=proposal_text)

        cost_value = calculate_cost(sample.duration_months, sample.expected_users)
        cost_text = normalize_cost(cost_value)
        safe_html = text_to_safe_html(proposal_text)

        LAST_PROPOSAL_TEXT = proposal_text
        LAST_PROPOSAL_HTML = safe_html
        LAST_COST = cost_text

        return HTMLResponse(content=build_html(safe_html, cost_text))

    except HTTPException as e:
        error_html = f"<div class='error'><b>Generator Error:</b> {escape(str(e.detail))}</div>"
        return HTMLResponse(
            content=build_html(error_html, "Not available"),
            status_code=e.status_code
        )

    except Exception as e:
        print("GET /generate-proposal error:", str(e))
        error_html = f"<div class='error'><b>Generator Error:</b> {escape(str(e))}</div>"
        return HTMLResponse(
            content=build_html(error_html, "Not available"),
            status_code=500
        )


# =====================================
# API GENERATE ROUTE FOR FRONTEND / SWAGGER
# =====================================
@app.post("/api/generate-proposal")
async def generate_post(data: ProposalRequest):
    global LAST_PROPOSAL_HTML, LAST_COST, LAST_PROPOSAL_TEXT

    try:
        prompt = build_prompt(data)
        result = generate_proposal(prompt)
        proposal_text = extract_proposal_html(result)

        if not proposal_text:
            raise HTTPException(
                status_code=500,
                detail="Generator returned empty output. Check app/generator.py response."
            )

        if is_generator_error(proposal_text):
            raise HTTPException(status_code=500, detail=proposal_text)

        cost_value = calculate_cost(data.duration_months, data.expected_users)
        cost_text = normalize_cost(cost_value)
        safe_html = text_to_safe_html(proposal_text)

        LAST_PROPOSAL_TEXT = proposal_text
        LAST_PROPOSAL_HTML = safe_html
        LAST_COST = cost_text

        return JSONResponse(
            content={
                "success": True,
                "project_title": data.project_title,
                "industry": data.industry,
                "duration_months": data.duration_months,
                "expected_users": data.expected_users,
                "tech_stack": data.tech_stack,
                "proposal": proposal_text,
                "proposal_html": safe_html,
                "cost": cost_text,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print("POST /api/generate-proposal error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =====================================
# KEEP OLD ROUTE ALSO FOR COMPATIBILITY
# =====================================
@app.post("/generate-proposal")
async def generate_post_compatibility(data: ProposalRequest):
    return await generate_post(data)


# =====================================
# DOWNLOAD LATEST GENERATED PDF
# =====================================
@app.get("/download-proposal")
async def download_proposal():
    global LAST_PROPOSAL_HTML, LAST_COST, LAST_PROPOSAL_TEXT

    try:
        if not LAST_PROPOSAL_TEXT or not LAST_COST:
            sample = ProposalRequest(
                project_title="AI Healthcare Platform",
                industry="Healthcare",
                duration_months=6,
                expected_users=5000,
                tech_stack=["Python", "FastAPI"]
            )

            prompt = build_prompt(sample)
            result = generate_proposal(prompt)
            proposal_text = extract_proposal_html(result)

            if not proposal_text:
                raise HTTPException(status_code=500, detail="No proposal available to download.")

            if is_generator_error(proposal_text):
                raise HTTPException(status_code=500, detail=proposal_text)

            cost_value = calculate_cost(sample.duration_months, sample.expected_users)
            cost_text = normalize_cost(cost_value)

            LAST_PROPOSAL_TEXT = proposal_text
            LAST_PROPOSAL_HTML = text_to_safe_html(proposal_text)
            LAST_COST = cost_text

        pdf_path = build_pdf(LAST_PROPOSAL_TEXT, LAST_COST)

        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename="Project_Proposal.pdf"
        )

    except HTTPException:
        raise
    except Exception as e:
        print("GET /download-proposal error:", str(e))
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


# =====================================
# OPTIONAL: GET LAST GENERATED OUTPUT
# =====================================
@app.get("/api/latest-proposal")
async def get_latest_proposal():
    global LAST_PROPOSAL_HTML, LAST_COST, LAST_PROPOSAL_TEXT

    if not LAST_PROPOSAL_TEXT:
        return JSONResponse(
            content={
                "success": False,
                "message": "No proposal generated yet."
            }
        )

    return JSONResponse(
        content={
            "success": True,
            "proposal": LAST_PROPOSAL_TEXT,
            "proposal_html": LAST_PROPOSAL_HTML,
            "cost": LAST_COST
        }
    )
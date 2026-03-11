import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import BaseModel
import google.generativeai as genai

from backend.tax_tools import FilingStatus, calculate_tax_result, explain_tax_result


app = FastAPI(title="Tax AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class TaxRequest(BaseModel):
    income: float
    filing_status: FilingStatus = "single"
    deductions: Optional[float] = None


class ExplainRequest(BaseModel):
    income: float
    filing_status: FilingStatus = "single"
    deductions: Optional[float] = None
    question: Optional[str] = None


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/calculate")
def calculate_route(req: TaxRequest) -> dict:
    try:
        return calculate_tax_result(req.income, req.filing_status, req.deductions)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.post("/api/explain")
async def explain_route(req: ExplainRequest) -> dict:
    try:
        result = calculate_tax_result(req.income, req.filing_status, req.deductions)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not configured.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    user_question = req.question or "Please explain this tax result in plain English."

    prompt = f"""You are a friendly, knowledgeable tax advisor assistant.

Tax calculation summary:
- Filing status: {result['filing_status'].title()}
- Gross income: ${result['income']:,.2f}
- Deductions applied: ${result['deductions_applied']:,.2f}
- Taxable income: ${result['taxable_income']:,.2f}
- Estimated federal tax owed: ${result['tax_owed']:,.2f}
- Effective tax rate: {result['effective_rate_percent']:.2f}%
- Top marginal bracket: {result['top_marginal_bracket']}

User question: {user_question}

Respond concisely. Remind the user this is a simplified estimate, not official tax advice.
"""

    try:
        response = model.generate_content(prompt)
        return {"explanation": response.text, "tax_result": result}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini API error: {exc}")


handler = Mangum(app, lifespan="off")

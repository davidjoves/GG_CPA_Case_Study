import os
import json
import subprocess
import sys
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.tax_tools import (
    FilingStatus,
    calculate_tax_result,
    explain_tax_result,
)
from backend.mcp.server import generate_mock_1040
from dotenv import load_dotenv

load_dotenv() 

app = FastAPI(title="Tax AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
    "https://gg-cpa-case-study.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
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


def _extract_agent_payload(agent_response: dict) -> dict:
    """
    Validate and extract the expected agent payload shape.

    Expected:
      {
        "summary": {
          "calculate_tax_response": {...},
          "generate_mock_1040_response": {...}
        },
        "explanation": "..."
      }
    """
    summary = agent_response.get("summary")
    if not isinstance(summary, dict):
        raise HTTPException(status_code=500, detail="Agent response missing summary.")

    calc = summary.get("calculate_tax_response")
    mock = summary.get("generate_mock_1040_response")
    if not isinstance(calc, dict):
        raise HTTPException(
            status_code=500,
            detail="Agent response missing calculate_tax_response.",
        )
    if not isinstance(mock, dict):
        raise HTTPException(
            status_code=500,
            detail="Agent response missing generate_mock_1040_response.",
        )

    return {"calc": calc, "mock": mock, "explanation": agent_response.get("explanation")}


def _unwrap_langchain_output(block: dict) -> dict:
    """
    The LangGraph agent sometimes returns tool results wrapped in a
    LangChain-style `{"output": [{"text": "...json..."}]}` structure.
    This helper unwraps that into a plain dict when possible.
    """
    if not isinstance(block, dict):
        return block

    output = block.get("output")
    if isinstance(output, list) and output:
        first = output[0]
        if isinstance(first, dict):
            text = first.get("text")
            if isinstance(text, str):
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    # Fall through to return original block.
                    pass
    return block


@app.post("/api/calculate")
async def calculate_route(req: TaxRequest) -> dict:
    """
    Run the AI agent once and return both the core tax
    calculation and the mock 1040 form from that single run.
    """
    agent = agent_run(
        AgentRequest(
            income=req.income,
            filing_status=req.filing_status,
            deductions=req.deductions,
        )
    )
    payload = _extract_agent_payload(agent)
    calc_raw = payload["calc"]
    mock_raw = payload["mock"]

    calc = _unwrap_langchain_output(calc_raw)
    mock = _unwrap_langchain_output(mock_raw)
    # The generate_mock_1040 tool returns a wrapper that includes
    # `mock_form`, `calculation`, and `summary`. The frontend only
    # needs `mock_form` for display.
    mock_form = mock.get("mock_form", mock)
    explanation_text = payload.get("explanation")
    if not isinstance(explanation_text, str) or not explanation_text.strip():
        explanation_text = explain_tax_result(
            income=req.income,
            filing_status=req.filing_status,
            deductions=req.deductions,
        )

    return {
        "calculate": calc,
        "mock_1040": mock_form,
        "explanation": explanation_text,
    }


@app.post("/api/mock-1040")
async def mock_1040_route(req: TaxRequest) -> dict:
    """
    Backwards-compatible endpoint that now simply reuses the
    single agent run used by /api/calculate.
    """
    combined = await calculate_route(req)
    return {"mock_form": combined["mock_1040"]}


class AgentRequest(BaseModel):
    income: float
    filing_status: FilingStatus = "single"
    deductions: Optional[float] = None


@app.post("/api/agent-run")
def agent_run(req: AgentRequest) -> dict:
    """
    Run the Tax AI Agent (Gemini + MCP tools) as a subprocess.

    This endpoint is intentionally heavy-weight and meant for the case study
    demo: it drives `client.py`, which in turn talks to the MCP server and
    returns a JSON object with both structured results and an explanation.
    """
    env = os.environ.copy()
    if "GOOGLE_API_KEY" not in env or not env["GOOGLE_API_KEY"]:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_API_KEY environment variable is required on the server.",
        )

    cmd = [
        sys.executable,
        "client.py",
        "--income",
        str(req.income),
        "--filing-status",
        req.filing_status,
    ]
    if req.deductions is not None:
        cmd.extend(["--deductions", str(req.deductions)])

    try:
        completed = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.dirname(__file__)),
            env=env,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Agent timed out.")

    if completed.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Agent failed: {completed.stderr.strip()}",
        )

    stdout = completed.stdout.strip()
    if not stdout:
        raise HTTPException(status_code=500, detail="Agent produced no output.")

    # First try to parse stdout as JSON directly.
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        return {"raw_output": stdout}

    # If the agent printed a list of content blocks, unwrap the first one.
    if isinstance(parsed, list) and parsed:
        first = parsed[0]
        if isinstance(first, dict) and "text" in first:
            text = first["text"]
            if isinstance(text, str):
                cleaned = text.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.removeprefix("```json").removeprefix("```")
                    if "```" in cleaned:
                        cleaned = cleaned.split("```", 1)[0]
                try:
                    inner = json.loads(cleaned)
                    if isinstance(inner, dict):
                        return inner
                except json.JSONDecodeError:
                    return {"raw_output": text}
        return {"raw_output": parsed}

    if isinstance(parsed, dict):
        return parsed

    return {"raw_output": parsed}


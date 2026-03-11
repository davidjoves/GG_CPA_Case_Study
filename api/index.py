import os
import json
import subprocess
import sys
from typing import Optional, Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from backend.tax_tools import FilingStatus
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


@app.post("/api/calculate")
async def calculate_route(req: TaxRequest) -> dict:
    agent = agent_run(
        AgentRequest(
            income=req.income,
            filing_status=req.filing_status,
            deductions=req.deductions,
        )
    )
    payload = _extract_agent_payload(agent)
    return payload["calc"]


@app.post("/api/mock-1040")
async def mock_1040_route(req: TaxRequest) -> dict:
    """
    Return a mock 1040-style representation driven by the MCP agent tools.
    """
    agent = agent_run(
        AgentRequest(
            income=req.income,
            filing_status=req.filing_status,
            deductions=req.deductions,
        )
    )
    payload = _extract_agent_payload(agent)
    return payload["mock"]


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


# Architecture Overview

This document describes the overall architecture of the **Tax AI Agent** case study: a full-stack application that collects tax intake data, runs an AI agent (Gemini + MCP tools), and displays estimated tax results and a mock Form 1040.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              User (Browser)                                   │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Next.js Frontend (port 3000)                                                │
│  • app/page.tsx           → Tax intake form (home)                            │
│  • app/results/page.tsx   → Results + mock 1040                               │
│  • components/            → TaxIntakeForm, SectionCard, FormField, etc.       │
│  • config.ts              → API base URL                                      │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ HTTP (POST /api/calculate)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  FastAPI Backend (port 8000) — api/index.py                                   │
│  • /api/health        → Liveness check                                        │
│  • /api/calculate     → Full run: agent → tax calc + mock 1040 + explanation  │
│  • /api/mock-1040     → Legacy; delegates to calculate                        │
│  • /api/agent-run     → Raw agent run (JSON from subprocess)                  │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ subprocess
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  client.py (CLI entry point)                                                  │
│  • Parses --income, --filing-status, --deductions                             │
│  • Connects to MCP server via stdio                                           │
│  • Builds LangGraph ReAct agent (Gemini) with MCP tools                       │
│  • Runs agent; parses tool results + explanation; prints single JSON          │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ stdio (MCP protocol)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  MCP Server — backend/mcp/server.py                                           │
│  • FastMCP "tax-agent" (stdio, json_response=True)                            │
│  • Tools: calculate_tax, explain_tax_result, sample_tax_scenarios,            │
│           generate_mock_1040                                                  │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Tax Calculator — backend/tax_tools/tax_calculator.py                         │
│  • STANDARD_DEDUCTION, BRACKETS (by filing status)                            │
│  • calculate_tax_result(), explain_tax_result(), sample_tax_scenarios()       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
ggcpa_case_study/
├── app/                      # Next.js App Router
│   ├── layout.tsx            # Root layout, fonts, metadata
│   ├── page.tsx              # Home: tax intake form with initial values from URL
│   ├── globals.css           # Global styles
│   └── results/
│       ├── page.tsx          # Server component: fetches /api/calculate, renders summary + mock 1040
│       └── ResultsActions.tsx # Client: Print / Save as PDF
├── api/
│   └── index.py              # FastAPI app: CORS, routes, subprocess bridge to client.py
├── components/
│   ├── TaxIntakeForm.tsx     # Client form: filing status, income, deductions, withheld; submits to /results?...
│   ├── SectionCard.tsx       # Collapsible section with status badge
│   └── FormField.tsx         # Label + description + input + error
├── types/                    # Next.js–generated and shared types
│   ├── routes.d.ts           # AppRouter route types (generated)
│   ├── validator.ts         # Page/layout type validation (generated)
│   └── cache-life.d.ts      # Cache typing (if used)
├── config.ts                 # API base URL and endpoint constants
├── client.py                 # MCP client + LangGraph agent; invoked by API as subprocess
├── backend/
│   ├── conftest.py           # Pytest conftest (adds backend/ to path)
│   ├── mcp/
│   │   └── server.py         # MCP server exposing tax tools over stdio
│   ├── tax_tools/
│   │   ├── __init__.py       # Re-exports from tax_calculator
│   │   └── tax_calculator.py # Core tax math and helpers
│   └── tests/
│       └── test_tax_calculator.py
├── requirements.txt          # Python deps (FastAPI, MCP, LangGraph, etc.)
├── package.json              # Next.js, React, Tailwind, scripts (dev, build, fastapi-dev)
├── Dockerfile                # Python image; runs uvicorn api.index:app
└── ARCHITECTURE.md           # This file
```

---

## Component Details

### 1. Frontend (Next.js 15, React 19, Tailwind 4)

| File | Role |
|------|------|
| **app/page.tsx** | Home page. Reads `searchParams` (income, deductions, withheld, filing_status, ui_status) and passes them as `initialValues` to `TaxIntakeForm` so the form can be pre-filled when returning from results. |
| **app/results/page.tsx** | Results page (server component). Calls `fetchResults(searchParams)` which POSTs to `API.CALCULATE` with income, deductions, filing_status. Renders summary (tax owed, taxable income, effective rate, refund/balance, top bracket) and mock 1040 lines. Handles errors and “Back to intake” link. |
| **components/TaxIntakeForm.tsx** | Client form. Manages filing status (single, married_joint, married_separate, head, qualifying_surviving_spouse), gross income, total deductions, federal withheld. Maps UI filing status to API `single` / `married`. On submit, validates and navigates to `/results?income=...&deductions=...&withheld=...&filing_status=...&ui_status=...`. |
| **config.ts** | `API_BASE_URL`: `NEXT_PUBLIC_API_BASE_URL` or `http://localhost:8000` in development. Exports `API.CALCULATE`, `API.MOCK_1040`, `API.AGENT_RUN`. |

### 2. API Layer (FastAPI — api/index.py)

- **CORS**: Allows `http://localhost:3000` and `https://gg-cpa-case-study.vercel.app`.
- **Models**: `TaxRequest`, `ExplainRequest`, `AgentRequest` (income, filing_status, optional deductions).
- **Routes**:
  - `GET /api/health` → `{ "status": "ok" }`.
  - `POST /api/calculate` → Main flow. Calls `agent_run()` with request body, then `_extract_agent_payload()` to get `calc`, `mock`, `explanation`. Unwraps LangChain-style tool output via `_unwrap_langchain_output()`. If the agent didn’t return an explanation, falls back to `explain_tax_result()`. Returns `{ calculate, mock_1040, explanation }`.
  - `POST /api/mock-1040` → Returns `{ mock_form }` from the same agent run as `/api/calculate`.
  - `POST /api/agent-run` → Runs `client.py` as a subprocess with `--income`, `--filing-status`, optional `--deductions`; requires `GOOGLE_API_KEY`. Parses stdout as JSON and returns it (handles list-of-blocks and raw_output shapes).
- **Helpers**: `_extract_agent_payload()` normalizes several agent response shapes (summary wrapper, top-level calc/mock_1040, flat keys, or raw_output). `_unwrap_langchain_output()` turns `{"output": [{"text": "..."}]}` into a dict when applicable.

### 3. Agent / MCP Client (client.py)

- **Role**: Entry point for the “Tax AI Agent” used by the web API. Not a long-running server; invoked per request by the API.
- **Flow**:
  1. Parse CLI args: `--income`, `--filing-status`, `--deductions`.
  2. Start MCP server via stdio: `python -m backend.mcp.server`.
  3. MCP handshake, then load MCP tools with `load_mcp_tools(session)`.
  4. Build Gemini LLM (`ChatGoogleGenerativeAI`, model `gemini-2.5-flash-lite`) and a LangGraph ReAct agent with those tools.
  5. Send a structured user message instructing the agent to call `calculate_tax` and `generate_mock_1040` once each, optionally `explain_tax_result`, and respond with a single JSON object: `{ summary: { calculate_tax_response, generate_mock_1040_response }, explanation }`.
  6. Extract tool results from the conversation and the final explanation; if both tool results are present, print that JSON; otherwise try to parse the last message content as JSON (including stripping markdown fences) and print one JSON object.
- **Output**: Single JSON object to stdout so the FastAPI bridge can parse it reliably.

### 4. MCP Server (backend/mcp/server.py)

- **Framework**: FastMCP with `json_response=True` for structured tool responses.
- **Transport**: stdio (default), used by `client.py`.
- **Tools**:
  - `calculate_tax(income, filing_status, deductions)` → delegates to `calculate_tax_result()`.
  - `explain_tax_result(...)` → human-readable explanation.
  - `sample_tax_scenarios()` → sample input/output pairs for testing.
  - `generate_mock_1040(...)` → builds a simplified 1040-style structure (lines, labels, values) plus calculation summary; used for UI and agent reasoning.

### 5. Tax Calculator (backend/tax_tools)

- **tax_calculator.py**:
  - `FilingStatus`: literal type for supported statuses.
  - `STANDARD_DEDUCTION`, `BRACKETS`: per-status tables (simplified, not official IRS).
  - `_compute_taxable_income()`: applies standard/itemized deduction and returns taxable income.
  - `_compute_tax_owed()`: progressive bracket math; returns (tax_owed, top_bracket_label).
  - `calculate_tax_result()`: public API; returns dict with income, filing_status, deductions_applied, taxable_income, tax_owed, effective_rate_percent, top_marginal_bracket.
  - `explain_tax_result()`: narrative summary for UI.
  - `sample_tax_scenarios()`: list of sample inputs and results for tests/agent.
- **__init__.py**: Re-exports for `from backend.tax_tools import ...`.

---

## Data Flow (Single Calculation)

1. User fills the intake form (filing status, gross income, deductions, withheld) and submits.
2. Next.js client navigates to `/results?income=...&deductions=...&withheld=...&filing_status=...&ui_status=...`.
3. Results page (server component) runs `fetchResults(params)` and POSTs to `API.CALCULATE` with `{ income, deductions, filing_status }`.
4. FastAPI receives the request, calls `agent_run(AgentRequest(...))`, which runs `client.py` in a subprocess with the same parameters.
5. `client.py` starts the MCP server, builds the ReAct agent with MCP tools, and sends the structured prompt. The agent calls `calculate_tax` and `generate_mock_1040` (and optionally `explain_tax_result`), then returns one JSON object.
6. `client.py` parses the conversation, extracts tool outputs and explanation, and prints one JSON object to stdout.
7. FastAPI reads stdout, parses JSON, runs `_extract_agent_payload()` and `_unwrap_langchain_output()`, and optionally fills in explanation via `explain_tax_result()` if missing. It returns `{ calculate, mock_1040, explanation }`.
8. Results page renders the summary and mock 1040; `ResultsActions` offers Print / Save as PDF.

---

## Key Technologies

| Layer | Technologies |
|-------|--------------|
| Frontend | Next.js 15 (App Router), React 19, Tailwind CSS 4, TypeScript |
| API | FastAPI, Pydantic, python-dotenv, CORS |
| Agent | LangGraph (ReAct), LangChain Google GenAI, MCP (stdio client/server), langchain-mcp-adapters |
| Tax logic | Pure Python in `backend/tax_tools` |
| Runtime | Node for Next.js (dev: `next dev`); Python 3.12 for API (uvicorn); Docker runs API only |

---

## Environment and Running the App

- **API**: Requires `GOOGLE_API_KEY` for the agent. Optional: `.env` with `GOOGLE_API_KEY` (and any other env); `load_dotenv()` is called in `api/index.py`.
- **Frontend**: Optional `NEXT_PUBLIC_API_BASE_URL`; defaults to `http://localhost:8000` in development.
- **Dev**: From repo root, `npm run dev` runs Next.js and FastAPI concurrently (`next dev` + `uvicorn api.index:app --reload --port 8000`). Frontend: 3000, API: 8000.
- **Production**: Dockerfile runs only the FastAPI app on port 8000. Next.js is typically built and served elsewhere (e.g. Vercel); it calls the deployed API using `NEXT_PUBLIC_API_BASE_URL`.

---

## Summary

The codebase is a **full-stack Tax AI Agent**: a Next.js front end for intake and results, a FastAPI backend that orchestrates a **single subprocess run of `client.py`** per calculation. That subprocess runs a **LangGraph ReAct agent** (Gemini) talking over stdio to an **MCP server** that exposes tax tools implemented on top of a **pure-Python tax calculator**. The API normalizes the agent’s JSON output and returns a unified `calculate` + `mock_1040` + `explanation` response for the results page.

"""
MCP Client for the Tax AI Agent.

This client:
  - Launches the stdio-based MCP server in `backend/mcp/server.py`
  - Loads the MCP tools (including `calculate_tax` and `generate_mock_1040`)
  - Wraps them in a LangGraph ReAct agent backed by Gemini
  - Accepts CLI arguments so the web API can drive it as a subprocess
  - Prints a single JSON object containing both structured results and an
    explanation that the case study can reference.
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Any, Dict

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI


def _build_model() -> ChatGoogleGenerativeAI:
    """Create the LLM used by the agent."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY environment variable is required.")


    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)


async def run_tax_agent_demo(
    *,
    income: float,
    filing_status: str,
    deductions: float | None,
) -> None:
    """
    Connect to the tax MCP server, create an agent, and run a demo query.

    This is a simple CLI entry point you can run with:

        GOOGLE_API_KEY=... python client.py
    """
    # Command to start the MCP server via stdio.
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "backend.mcp.server"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Perform the MCP handshake.
            await session.initialize()

            # Load all tools exposed by the tax MCP server.
            tools = await load_mcp_tools(session)

            # Build the LLM and the ReAct-style agent with these tools.
            model = _build_model()
            agent = create_react_agent(model, tools)

            # Ask the agent to call calculate_tax + generate_mock_1040 for
            # the provided inputs and return a single JSON object.
            user_message = (
                "You are a tax-return agent with access to tools like "
                "`calculate_tax`, `generate_mock_1040`, and `explain_tax_result`.\n\n"
                f"For a filer with filing_status = {filing_status!r}, "
                f"income = {income}, and deductions = {deductions}:\n"
                "1) Use the tools to compute the tax owed and key numbers.\n"
                "2) Generate a mock 1040-style layout.\n"
                "3) Respond with TWO sections:\n"
                "   (A) A JSON object under the key `summary` containing the raw "
                "numbers and mock form structure you obtained from the tools.\n"
                "   (B) A short, human-friendly explanation under the key "
                "`explanation`.\n"
                "Return your final answer as a single JSON object like:\n"
                "{ \"summary\": { ... }, \"explanation\": \"...\" }"
            )

            result: Dict[str, Any] = await agent.ainvoke(
                {"messages": [("user", user_message)]}
            )
            final_messages = result.get("messages", [])
            if not final_messages:
                print("Agent returned no messages.")
                return

            last = final_messages[-1]
            content = getattr(last, "content", last)

            # Ensure we always print a single JSON object to stdout so that
            # the FastAPI bridge can parse it reliably.
            if isinstance(content, str):
                cleaned = content.strip()
                # Strip markdown code fences if the model included them.
                if cleaned.startswith("```"):
                    cleaned = cleaned.removeprefix("```json").removeprefix("```")
                    if "```" in cleaned:
                        cleaned = cleaned.split("```", 1)[0]
                    cleaned = cleaned.strip()

                try:
                    parsed = json.loads(cleaned)
                except json.JSONDecodeError:
                    parsed = {"explanation": content}
            else:
                parsed = content

            print(json.dumps(parsed))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Tax AI Agent via MCP.")
    parser.add_argument("--income", type=float, required=True)
    parser.add_argument("--filing-status", type=str, required=True)
    parser.add_argument("--deductions", type=float, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    asyncio.run(
        run_tax_agent_demo(
            income=args.income,
            filing_status=args.filing_status,
            deductions=args.deductions,
        )
    )


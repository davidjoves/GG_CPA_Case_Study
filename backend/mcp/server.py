from mcp.server.fastmcp import FastMCP

from backend.tax_tools import (
    FilingStatus,
    calculate_tax_result,
    explain_tax_result as explain_tax_explanation,
    sample_tax_scenarios as sample_tax_scenarios_impl,
)


# json_response=True ensures MCP clients (including our FastAPI bridge)
# receive structuredContent with JSON data for each tool call.
mcp = FastMCP("tax-agent", json_response=True)


@mcp.tool()
def calculate_tax(
    income: float,
    filing_status: FilingStatus = "single",
    deductions: float | None = None,
) -> dict:
    """
    MCP tool wrapper around the core tax calculation helper.
    """
    return calculate_tax_result(
        income=income,
        filing_status=filing_status,
        deductions=deductions,
    )


@mcp.tool()
def explain_tax_result(
    income: float,
    filing_status: FilingStatus = "single",
    deductions: float | None = None,
) -> str:
    """
    MCP tool wrapper that returns a human-readable explanation.
    """
    return explain_tax_explanation(
        income=income,
        filing_status=filing_status,
        deductions=deductions,
    )


@mcp.tool()
def sample_tax_scenarios() -> list[dict]:
    """
    MCP tool wrapper that returns a small set of sample scenarios.
    """
    return sample_tax_scenarios_impl()


@mcp.tool()
def generate_mock_1040(
    income: float,
    filing_status: FilingStatus = "single",
    deductions: float | None = None,
) -> dict:
    """
    Produce a simplified, 1040-style representation of the return.

    This is designed both for the web UI (printable view) and for the
    AI agent to reason about a mock 1040 layout.
    """
    base = calculate_tax_result(
        income=income,
        filing_status=filing_status,
        deductions=deductions,
    )

    lines: list[dict] = [
        {
            "line": "1",
            "label": "Wages, salaries, tips, etc.",
            "value": base["income"],
        },
        {
            "line": "9",
            "label": "Total income",
            "value": base["income"],
        },
        {
            "line": "12",
            "label": "Standard or itemized deductions",
            "value": base["deductions_applied"],
        },
        {
            "line": "15",
            "label": "Taxable income",
            "value": base["taxable_income"],
        },
        {
            "line": "16",
            "label": "Tax",
            "value": base["tax_owed"],
        },
    ]

    summary = {
        "filing_status": base["filing_status"],
        "effective_rate_percent": base["effective_rate_percent"],
        "top_marginal_bracket": base["top_marginal_bracket"],
    }

    return {
        "mock_form": {
            "title": "Mock Form 1040 (Simplified)",
            "tax_year": 2024,
            "lines": lines,
        },
        "calculation": base,
        "summary": summary,
    }


if __name__ == "__main__":
    # Default transport is stdio, which is what MCP clients expect.
    mcp.run()


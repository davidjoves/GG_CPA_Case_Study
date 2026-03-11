from mcp.server.fastmcp import FastMCP

from tax_tools import (
    FilingStatus,
    calculate_tax_result,
    explain_tax_result as explain_tax_explanation,
    sample_tax_scenarios as sample_tax_scenarios_impl,
)


mcp = FastMCP("tax-agent")


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


if __name__ == "__main__":
    # Default transport is stdio, which is what MCP clients expect.
    mcp.run()


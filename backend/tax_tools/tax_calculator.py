from typing import Literal, List, Dict


FilingStatus = Literal[
    "single",
    "married",
    "married_joint",
    "married_separate",
    "head",
    "qualifying_surviving_spouse",
]


# For this prototype, we give each supported filing status an explicit
# standard deduction and bracket table, even when some share the same
# underlying numbers. This keeps the tax logic aligned with the UI
# statuses surfaced in the intake form.
STANDARD_DEDUCTION: Dict[FilingStatus, float] = {
    # Single and Head of Household use the "single" baseline in this simplified model.
    "single": 13850.0,
    "head": 13850.0,
    # Married-related statuses share the "married" baseline here.
    "married": 27700.0,
    "married_joint": 27700.0,
    "married_separate": 27700.0,
    "qualifying_surviving_spouse": 27700.0,
}


# Very simplified progressive brackets for each status
# (example numbers, not real IRS tables).
BRACKETS: Dict[FilingStatus, List[tuple[float, float, float]]] = {
    "single": [
        (0.0, 11000.0, 0.10),
        (11000.0, 44725.0, 0.12),
        (44725.0, 95375.0, 0.22),
        (95375.0, float("inf"), 0.24),
    ],
    "head": [
        (0.0, 11000.0, 0.10),
        (11000.0, 44725.0, 0.12),
        (44725.0, 95375.0, 0.22),
        (95375.0, float("inf"), 0.24),
    ],
    "married": [
        (0.0, 22000.0, 0.10),
        (22000.0, 89450.0, 0.12),
        (89450.0, 190750.0, 0.22),
        (190750.0, float("inf"), 0.24),
    ],
    "married_joint": [
        (0.0, 22000.0, 0.10),
        (22000.0, 89450.0, 0.12),
        (89450.0, 190750.0, 0.22),
        (190750.0, float("inf"), 0.24),
    ],
    "married_separate": [
        (0.0, 22000.0, 0.10),
        (22000.0, 89450.0, 0.12),
        (89450.0, 190750.0, 0.22),
        (190750.0, float("inf"), 0.24),
    ],
    "qualifying_surviving_spouse": [
        (0.0, 22000.0, 0.10),
        (22000.0, 89450.0, 0.12),
        (89450.0, 190750.0, 0.22),
        (190750.0, float("inf"), 0.24),
    ],
}


def _compute_taxable_income(
    income: float, filing_status: FilingStatus, deductions: float | None
) -> float:
    if filing_status not in STANDARD_DEDUCTION:
        raise ValueError(
            'filing_status must be one of '
            '"single", "married", "married_joint", "married_separate", '
            '"head", or "qualifying_surviving_spouse".'
        )
    std_deduction = STANDARD_DEDUCTION[filing_status]
    applied_deduction = max(deductions or 0.0, std_deduction)
    taxable_income = max(0.0, income - applied_deduction)
    return taxable_income


def _compute_tax_owed(
    taxable_income: float, filing_status: FilingStatus
) -> tuple[float, str]:
    if filing_status not in BRACKETS:
        raise ValueError(
            'filing_status must be one of '
            '"single", "married", "married_joint", "married_separate", '
            '"head", or "qualifying_surviving_spouse".'
        )
    brackets = BRACKETS[filing_status]
    remaining = taxable_income
    tax = 0.0
    last_bracket_label = "0%"

    for lower, upper, rate in brackets:
        if remaining <= 0:
            break

        band_size = upper - lower
        if taxable_income <= lower:
            break

        income_in_band = min(remaining, band_size)
        tax += income_in_band * rate
        remaining -= income_in_band
        last_bracket_label = f"{int(rate * 100)}%"

    return tax, last_bracket_label


def calculate_tax_result(
    income: float,
    filing_status: FilingStatus = "single",
    deductions: float | None = None,
) -> dict:
    if income < 0:
        raise ValueError("Income must be non-negative.")

    if filing_status not in STANDARD_DEDUCTION:
        raise ValueError(
            'filing_status must be one of '
            '"single", "married", "married_joint", "married_separate", '
            '"head", or "qualifying_surviving_spouse".'
        )

    taxable_income = _compute_taxable_income(income, filing_status, deductions)
    tax_owed, top_bracket = _compute_tax_owed(taxable_income, filing_status)

    effective_rate = (tax_owed / income * 100.0) if income > 0 else 0.0
    deductions_applied = income - taxable_income

    return {
        "income": round(income, 2),
        "filing_status": filing_status,
        "deductions_applied": round(deductions_applied, 2),
        "taxable_income": round(taxable_income, 2),
        "tax_owed": round(tax_owed, 2),
        "effective_rate_percent": round(effective_rate, 2),
        "top_marginal_bracket": top_bracket,
    }


def explain_tax_result(
    income: float,
    filing_status: FilingStatus = "single",
    deductions: float | None = None,
) -> str:
    """
    Human-readable explanation of the tax calculation for UI display.

    This wraps the calculate_tax_result helper and produces a concise narrative
    that can be shown directly to the user.
    """
    result = calculate_tax_result(
        income=income,
        filing_status=filing_status,
        deductions=deductions,
    )

    lines = [
        f"Filing status: {result['filing_status'].title()}",
        f"Gross income: ${result['income']:,.2f}",
        f"Deductions applied: ${result['deductions_applied']:,.2f}",
        f"Taxable income: ${result['taxable_income']:,.2f}",
        f"Estimated federal tax owed: ${result['tax_owed']:,.2f}",
        f"Effective tax rate: {result['effective_rate_percent']:.2f}%",
        f"Top marginal bracket reached: {result['top_marginal_bracket']}",
        "",
        "Note: This is a simplified illustration for the case study prototype,",
        "not a substitute for real tax advice or official IRS calculations.",
    ]

    return "\n".join(lines)


def sample_tax_scenarios() -> list[dict]:
    """
    Provide a few sample input/output pairs for testing the calculator.

    This can be used by the agent or tests to quickly verify that the
    tax calculation logic behaves as expected for a handful of cases.
    """
    samples: list[dict] = []
    test_inputs = [
        {"income": 40_000.0, "filing_status": "single", "deductions": None},
        {"income": 90_000.0, "filing_status": "single", "deductions": 20_000.0},
        {"income": 60_000.0, "filing_status": "married", "deductions": None},
        {"income": 150_000.0, "filing_status": "married", "deductions": 10_000.0},
    ]

    for case in test_inputs:
        calc = calculate_tax_result(
            income=case["income"],
            filing_status=case["filing_status"],  # type: ignore[arg-type]
            deductions=case["deductions"],
        )
        samples.append({"input": case, "result": calc})

    return samples


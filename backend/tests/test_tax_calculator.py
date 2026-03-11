import math

import pytest

from tax_tools import (
    FilingStatus,
    STANDARD_DEDUCTION,
    calculate_tax_result,
    explain_tax_result,
    sample_tax_scenarios,
)


def test_calculate_tax_basic_single() -> None:
    result = calculate_tax_result(40_000.0, filing_status="single", deductions=None)

    assert result["income"] == 40_000.0
    assert result["filing_status"] == "single"

    # 40,000 - standard deduction 13,850 = 26,150 taxable
    assert result["taxable_income"] == 26_150.0

    # Tax: 11,000 @10% = 1,100; remaining 15,150 @12% = 1,818; total = 2,918
    assert math.isclose(result["tax_owed"], 2_918.0, rel_tol=1e-6)
    assert result["top_marginal_bracket"] == "12%"


def test_negative_income_raises() -> None:
    with pytest.raises(ValueError):
        calculate_tax_result(-1.0, filing_status="single", deductions=None)


def test_invalid_filing_status_raises() -> None:
    with pytest.raises(ValueError):
        calculate_tax_result(10_000.0, filing_status="invalid", deductions=None)  # type: ignore[arg-type]


def test_standard_deduction_applied_when_greater_than_itemized() -> None:
    income = 50_000.0
    filing_status: FilingStatus = "married"
    small_deductions = 1_000.0

    result_small_deductions = calculate_tax_result(
        income=income,
        filing_status=filing_status,
        deductions=small_deductions,
    )
    result_no_deductions = calculate_tax_result(
        income=income,
        filing_status=filing_status,
        deductions=None,
    )

    assert result_small_deductions["taxable_income"] == result_no_deductions["taxable_income"]
    assert result_no_deductions["deductions_applied"] == STANDARD_DEDUCTION[filing_status]


def test_explain_tax_result_includes_key_fields() -> None:
    explanation = explain_tax_result(40_000.0, filing_status="single", deductions=None)

    assert "Filing status" in explanation
    assert "Gross income" in explanation
    assert "Estimated federal tax owed" in explanation


def test_sample_tax_scenarios_shape_and_count() -> None:
    samples = sample_tax_scenarios()

    assert len(samples) == 4
    for sample in samples:
        assert "input" in sample
        assert "result" in sample


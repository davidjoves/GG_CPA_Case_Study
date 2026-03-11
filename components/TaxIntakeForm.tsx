"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { SectionCard } from "./SectionCard";
import { FormField } from "./FormField";

type FilingStatus =
  | "single"
  | "married_joint"
  | "married_separate"
  | "head"
  | "qualifying_surviving_spouse";

type TaxFormValues = {
  filingStatus: FilingStatus | "";
  grossIncome: string;
  totalDeductions: string;
  federalWithheld: string;
};

type TaxIntakeFormProps = {
  initialValues?: Partial<TaxFormValues>;
};

type TaxFormErrors = Partial<Record<keyof TaxFormValues, string>>;

export function TaxIntakeForm({ initialValues }: TaxIntakeFormProps) {
  const router = useRouter();
  const [values, setValues] = useState<TaxFormValues>({
    filingStatus: (initialValues?.filingStatus as FilingStatus | "") ?? "",
    grossIncome: initialValues?.grossIncome ?? "",
    totalDeductions: initialValues?.totalDeductions ?? "",
    federalWithheld: initialValues?.federalWithheld ?? "",
  });
  const [errors, setErrors] = useState<TaxFormErrors>({});
  const [submitting, setSubmitting] = useState(false);

  const updateField = (field: keyof TaxFormValues, value: string) => {
    setValues((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: undefined }));
  };

  const mapFilingStatusToApi = (status: FilingStatus): "single" | "married" => {
    if (status === "married_joint" || status === "married_separate") {
      return "married";
    }
    if (status === "qualifying_surviving_spouse") {
      return "married";
    }
    if (status === "head") {
      return "single";
    }
    return status;
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const nextErrors: TaxFormErrors = {};

    if (!values.filingStatus) {
      nextErrors.filingStatus = "Select a filing status.";
    }

    const numericFields: Array<keyof TaxFormValues> = [
      "grossIncome",
      "totalDeductions",
      "federalWithheld",
    ];

    numericFields.forEach((field) => {
      const raw = values[field];
      if (!raw) {
        nextErrors[field] = "This field is required.";
        return;
      }
      const parsed = Number(raw);
      if (Number.isNaN(parsed)) {
        nextErrors[field] = "Enter a valid number.";
      } else if (parsed < 0) {
        nextErrors[field] = "Value cannot be negative.";
      }
    });

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      return;
    }

    if (!values.filingStatus) {
      return;
    }

    const income = Number(values.grossIncome);
    const deductions = Number(values.totalDeductions);
    const withheld = Number(values.federalWithheld);

    setSubmitting(true);

    // Navigate to dedicated results page, passing inputs via query string,
    // including the UI filing status so it can be restored when navigating back.
    const params = new URLSearchParams({
      income: String(income),
      deductions: String(deductions),
      withheld: String(withheld),
      filing_status: mapFilingStatusToApi(values.filingStatus),
      ui_status: values.filingStatus || "",
    });
    router.push(`/results?${params.toString()}`);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-4 sm:gap-5"
      noValidate
    >
      <SectionCard
        title="Tax data collection"
        description="Provide the core numbers we need to estimate your tax outcome."
        number="1"
        status="in-progress"
        defaultOpen
      >
        <div className="space-y-6">
          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-600">
              Filing status
            </p>
            <div className="grid gap-2 md:grid-cols-3">
              <label className="flex cursor-pointer items-start gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-xs transition hover:border-sky-400">
                <input
                  type="radio"
                  name="filingStatus"
                  value="single"
                  checked={values.filingStatus === "single"}
                  onChange={() => updateField("filingStatus", "single")}
                  className="mt-1 h-4 w-4 border-slate-300 text-sky-600 focus:ring-sky-500"
                />
                <span>
                  <span className="font-medium">Single</span>
                  <span className="block text-xs text-slate-500">
                    Filing on your own.
                  </span>
                </span>
              </label>
              <label className="flex cursor-pointer items-start gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-xs transition hover:border-sky-400">
                <input
                  type="radio"
                  name="filingStatus"
                  value="married_joint"
                  checked={values.filingStatus === "married_joint"}
                  onChange={() => updateField("filingStatus", "married_joint")}
                  className="mt-1 h-4 w-4 border-slate-300 text-sky-600 focus:ring-sky-500"
                />
                <span>
                  <span className="font-medium">Married filing jointly</span>
                  <span className="block text-xs text-slate-500">
                    Married and filing one return together. Often most
                    beneficial for couples.
                  </span>
                </span>
              </label>
              <label className="flex cursor-pointer items-start gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-xs transition hover:border-sky-400">
                <input
                  type="radio"
                  name="filingStatus"
                  value="married_separate"
                  checked={values.filingStatus === "married_separate"}
                  onChange={() => updateField("filingStatus", "married_separate")}
                  className="mt-1 h-4 w-4 border-slate-300 text-sky-600 focus:ring-sky-500"
                />
                <span>
                  <span className="font-medium">Married filing separately</span>
                  <span className="block text-xs text-slate-500">
                    Married but filing individual returns. Useful in specific
                    situations.
                  </span>
                </span>
              </label>
              <label className="flex cursor-pointer items-start gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-xs transition hover:border-sky-400">
                <input
                  type="radio"
                  name="filingStatus"
                  value="head"
                  checked={values.filingStatus === "head"}
                  onChange={() => updateField("filingStatus", "head")}
                  className="mt-1 h-4 w-4 border-slate-300 text-sky-600 focus:ring-sky-500"
                />
                <span>
                  <span className="font-medium">Head of household</span>
                  <span className="block text-xs text-slate-500">
                    Unmarried and paid more than half the cost of keeping up a
                    home for yourself and a qualifying dependent.
                  </span>
                </span>
              </label>
              <label className="flex cursor-pointer items-start gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-xs transition hover:border-sky-400">
                <input
                  type="radio"
                  name="filingStatus"
                  value="qualifying_surviving_spouse"
                  checked={
                    values.filingStatus === "qualifying_surviving_spouse"
                  }
                  onChange={() =>
                    updateField("filingStatus", "qualifying_surviving_spouse")
                  }
                  className="mt-1 h-4 w-4 border-slate-300 text-sky-600 focus:ring-sky-500"
                />
                <span>
                  <span className="font-medium">Qualifying surviving spouse</span>
                  <span className="block text-xs text-slate-500">
                    Spouse died in the last 2 years and you have a dependent
                    child and meet IRS tests.
                  </span>
                </span>
              </label>
            </div>
            {errors.filingStatus && (
              <p className="text-xs font-medium text-red-600">
                {errors.filingStatus}
              </p>
            )}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              id="grossIncome"
              name="grossIncome"
              type="number"
              min={0}
              step="0.01"
              label="Gross annual income"
              description="Total wages and salary for the tax year."
              placeholder="0.00"
              value={values.grossIncome}
              onChange={(e) => updateField("grossIncome", e.target.value)}
              error={errors.grossIncome}
            />
            <FormField
              id="totalDeductions"
              name="totalDeductions"
              type="number"
              min={0}
              step="0.01"
              label="Total deductions"
              description="Standard or itemized deductions you plan to claim."
              placeholder="0.00"
              value={values.totalDeductions}
              onChange={(e) => updateField("totalDeductions", e.target.value)}
              error={errors.totalDeductions}
            />
            <FormField
              id="federalWithheld"
              name="federalWithheld"
              type="number"
              min={0}
              step="0.01"
              label="Federal tax withheld"
              description="Total federal income tax withheld from paychecks and forms."
              placeholder="0.00"
              value={values.federalWithheld}
              onChange={(e) => updateField("federalWithheld", e.target.value)}
              error={errors.federalWithheld}
            />
          </div>
        </div>
      </SectionCard>

      <div className="space-y-3 border-t border-slate-200 bg-slate-50/80 px-4 py-4 sm:rounded-b-xl sm:px-6">
        <div className="flex flex-wrap items-center justify-end gap-2">
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center justify-center rounded-full bg-sky-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-50"
          >
            {submitting ? "Calculating..." : "Calculate estimate"}
          </button>
        </div>
      </div>
    </form>
  );
}


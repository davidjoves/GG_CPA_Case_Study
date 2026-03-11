"use client";

export function ResultsActions(props: {
  income: number;
  deductions: number;
  filingStatus: "single" | "married";
}) {
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => window.print()}
          className="inline-flex items-center justify-center rounded-full bg-slate-900 px-5 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-slate-800"
        >
          Print / Save as PDF
        </button>
      </div>
    </div>
  );
}


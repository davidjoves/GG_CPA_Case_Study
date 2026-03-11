"use client";

import { useState } from "react";
import { API } from "../../config";

export function ResultsActions(props: {
  income: number;
  deductions: number;
  filingStatus: "single" | "married";
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<string | null>(null);

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
        <button
          type="button"
          disabled={loading}
          onClick={async () => {
            setLoading(true);
            setError(null);
            setExplanation(null);
            try {
              const res = await fetch(API.AGENT_RUN, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  income: props.income,
                  filing_status: props.filingStatus,
                  deductions: props.deductions,
                }),
              });

              const data = (await res.json()) as
                | { explanation?: string }
                | { raw_output?: string }
                | { detail?: string };

              if (!res.ok) {
                throw new Error(
                  ("detail" in data && data.detail) ||
                    "Agent request failed. Check the API logs.",
                );
              }

              if ("explanation" in data && data.explanation) {
                setExplanation(data.explanation);
                return;
              }

              if ("raw_output" in data && data.raw_output) {
                setExplanation(data.raw_output);
                return;
              }

              setExplanation(JSON.stringify(data, null, 2));
            } catch (e) {
              setError(e instanceof Error ? e.message : "Agent request failed.");
            } finally {
              setLoading(false);
            }
          }}
          className="inline-flex items-center justify-center rounded-full bg-sky-600 px-5 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Asking AI agent..." : "Ask AI agent to explain"}
        </button>
      </div>

      {error && <p className="text-xs font-medium text-red-600">{error}</p>}

      {explanation && (
        <div className="rounded-xl border border-slate-200 bg-white p-3 text-xs text-slate-800 shadow-sm">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Agent explanation
          </p>
          <pre className="mt-2 whitespace-pre-wrap font-sans leading-relaxed">
            {explanation}
          </pre>
        </div>
      )}
    </div>
  );
}


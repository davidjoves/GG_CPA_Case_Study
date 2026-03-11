import { TaxIntakeForm } from "../components/TaxIntakeForm";

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-100 font-sans text-slate-900">
      <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8 lg:py-10">
        <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div className="text-center sm:text-left">
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
              AI TAX RETURN AGENT
            </p>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
              Tax Intake Summary
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              Review and complete the sections below to share the information we
              need to prepare a simple tax return. You can save your progress at
              any time.
            </p>
          </div>

        </header>

        <section className="flex justify-center">
          <div className="w-full max-w-3xl space-y-4">
            <div className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-700">
              <div>
                <span className="font-semibold text-slate-900">
                  Prototype status:
                </span>{" "}
                In progress
              </div>
              <div className="h-4 w-px bg-slate-300" />
              <div>
                <span className="font-semibold text-slate-900">
                  Last updated:
                </span>{" "}
                Today
              </div>
              <div className="h-4 w-px bg-slate-300" />
              <div>
                <span className="font-semibold text-slate-900">
                  Submission:
                </span>{" "}
                Draft 1
              </div>
            </div>

            <TaxIntakeForm />
          </div>
        </section>
      </main>
    </div>
  );
}

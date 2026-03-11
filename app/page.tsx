import { TaxIntakeForm } from "../components/TaxIntakeForm";

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-100 font-sans text-slate-900">
      <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8 lg:py-10">
        <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div>
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
          <div className="flex items-start gap-3">
            <button className="hidden rounded-full border border-slate-300 bg-white px-4 py-2 text-xs font-medium text-slate-700 shadow-sm hover:bg-slate-50 sm:inline-flex">
              Print intake summary
            </button>
          </div>
        </header>

        <section className="grid gap-6 lg:grid-cols-[minmax(0,2.3fr)_minmax(0,1fr)]">
          <div className="space-y-4">
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

          <aside className="space-y-4">
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="text-sm font-semibold text-slate-900">
                View your tax results
              </h2>
              <p className="mt-1 text-xs text-slate-600">
                Once you complete the intake, we will calculate an estimated tax
                owed or refund due using a simplified tax model.
              </p>
              <button className="mt-3 inline-flex w-full items-center justify-center rounded-full bg-sky-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-sky-700">
                Visit Tax Summary (coming soon)
              </button>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="text-sm font-semibold text-slate-900">
                Learn about this prototype
              </h2>
              <p className="mt-1 text-xs text-slate-600">
                This interface is part of the GreenGrowth CPAs AI Intern case
                study. It mimics the feel of a guided government form while
                staying focused on a simple tax scenario.
              </p>
            </div>
          </aside>
        </section>
      </main>
    </div>
  );
}

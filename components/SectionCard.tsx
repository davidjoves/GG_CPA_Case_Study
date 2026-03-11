"use client";

import { ReactNode, useState } from "react";

type SectionCardProps = {
  number?: string;
  title: string;
  description?: string;
  status?: "not-started" | "in-progress" | "completed";
  defaultOpen?: boolean;
  children: ReactNode;
};

const statusStyles: Record<
  NonNullable<SectionCardProps["status"]>,
  { label: string; className: string }
> = {
  "not-started": {
    label: "Not started",
    className: "bg-slate-100 text-slate-700",
  },
  "in-progress": {
    label: "In progress",
    className: "bg-blue-50 text-blue-700",
  },
  completed: {
    label: "Completed",
    className: "bg-emerald-50 text-emerald-700",
  },
};

export function SectionCard({
  number,
  title,
  description,
  status = "not-started",
  defaultOpen = false,
  children,
}: SectionCardProps) {
  const [open, setOpen] = useState(defaultOpen);

  const statusMeta = statusStyles[status];

  return (
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex w-full items-center justify-between px-5 py-4 text-left"
      >
        <div className="flex items-center gap-4">
          {number && (
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-sky-600 text-sm font-semibold text-white">
              {number}
            </div>
          )}
          <div>
            <h2 className="text-sm font-semibold tracking-tight text-slate-900">
              {title}
            </h2>
            {description && (
              <p className="mt-1 text-xs text-slate-500">{description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          {statusMeta && (
            <span
              className={`hidden rounded-full px-3 py-1 text-xs font-medium sm:inline-flex ${statusMeta.className}`}
            >
              {statusMeta.label}
            </span>
          )}
          <span
            aria-hidden="true"
            className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-slate-200 bg-slate-50 text-slate-500"
          >
            <svg
              className={`h-3 w-3 transform transition-transform ${
                open ? "rotate-180" : ""
              }`}
              viewBox="0 0 16 16"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M4 6L8 10L12 6"
                stroke="currentColor"
                strokeWidth="1.4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
        </div>
      </button>
      {open && (
        <div className="border-t border-slate-200 bg-slate-50 px-5 py-4 sm:px-6 sm:py-5">
          {children}
        </div>
      )}
    </section>
  );
}


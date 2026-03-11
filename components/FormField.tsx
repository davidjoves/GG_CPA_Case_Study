"use client";

import { InputHTMLAttributes, ReactNode } from "react";

type FormFieldProps = {
  id: string;
  label: string;
  description?: string;
  children?: ReactNode;
  error?: string;
} & InputHTMLAttributes<HTMLInputElement>;

export function FormField({
  id,
  label,
  description,
  children,
  error,
  className = "",
  ...inputProps
}: FormFieldProps) {
  const baseClasses =
    "block w-full rounded-lg border bg-white px-3 py-2 text-sm text-slate-900 shadow-xs outline-none ring-0 transition placeholder:text-slate-400";
  const focusClasses = "focus:border-sky-500 focus:ring-2 focus:ring-sky-200";
  const borderClasses = error
    ? "border-red-400 focus:border-red-500 focus:ring-red-200"
    : "border-slate-300 " + focusClasses;
  const sharedClasses = `${baseClasses} ${borderClasses}`;

  return (
    <div className="space-y-1.5">
      <label
        htmlFor={id}
        className="text-xs font-medium uppercase tracking-wide text-slate-600"
      >
        {label}
      </label>
      {description && (
        <p className="text-xs text-slate-500">{description}</p>
      )}
      {children ? (
        children
      ) : (
        <input id={id} className={`${sharedClasses} ${className}`} {...inputProps} />
      )}
      {error && (
        <p className="text-xs font-medium text-red-600">{error}</p>
      )}
    </div>
  );
}


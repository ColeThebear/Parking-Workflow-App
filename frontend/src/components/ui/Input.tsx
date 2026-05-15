import type { InputHTMLAttributes, SelectHTMLAttributes, ReactNode } from "react";

const BASE_INPUT =
  "w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 " +
  "placeholder:text-gray-400 shadow-sm " +
  "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 " +
  "disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed " +
  "transition-colors duration-150";

interface LabelProps {
  label?: string;
  hint?: string;
  error?: string;
  children: ReactNode;
}

function FieldWrapper({ label, hint, error, children }: LabelProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label className="text-sm font-medium text-gray-700">{label}</label>
      )}
      {children}
      {hint && !error && <p className="text-xs text-gray-500">{hint}</p>}
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}

// ── TextInput ────────────────────────────────────────────────────────────────

interface TextInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
}

export function TextInput({ label, hint, error, className = "", ...props }: TextInputProps) {
  return (
    <FieldWrapper label={label} hint={hint} error={error}>
      <input
        className={`${BASE_INPUT} ${error ? "border-red-400 focus:ring-red-400" : ""} ${className}`}
        {...props}
      />
    </FieldWrapper>
  );
}

// ── SelectInput ──────────────────────────────────────────────────────────────

interface SelectInputProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  hint?: string;
  error?: string;
  children: ReactNode;
}

export function SelectInput({ label, hint, error, className = "", children, ...props }: SelectInputProps) {
  return (
    <FieldWrapper label={label} hint={hint} error={error}>
      <select
        className={`${BASE_INPUT} ${error ? "border-red-400 focus:ring-red-400" : ""} ${className}`}
        {...props}
      >
        {children}
      </select>
    </FieldWrapper>
  );
}

import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";
import { useId } from "react";

const cx = (...parts: Array<string | false | undefined>) => parts.filter(Boolean).join(" ");

export function Button({
  variant = "primary",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "danger" }) {
  const styles = {
    primary: "bg-brand-600 text-white hover:bg-brand-700 disabled:bg-brand-400",
    secondary: "bg-white text-brand-700 ring-1 ring-inset ring-slate-300 hover:bg-slate-50",
    danger: "bg-red-600 text-white hover:bg-red-700",
  }[variant];
  return (
    <button
      className={cx(
        "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold",
        "transition-colors disabled:cursor-not-allowed disabled:opacity-70",
        styles,
        className,
      )}
      {...props}
    />
  );
}

export function Field({
  label,
  error,
  hint,
  children,
}: {
  label: string;
  error?: string;
  hint?: string;
  children: (props: { id: string; describedBy: string | undefined; invalid: boolean }) => ReactNode;
}) {
  const id = useId();
  const hintId = `${id}-hint`;
  const errId = `${id}-err`;
  const describedBy = cx(hint && hintId, error && errId) || undefined;
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-slate-700">
        {label}
      </label>
      {children({ id, describedBy, invalid: Boolean(error) })}
      {hint && (
        <p id={hintId} className="text-xs text-slate-500">
          {hint}
        </p>
      )}
      {error && (
        <p id={errId} role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}

export function TextInput({
  invalid,
  className,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { invalid?: boolean }) {
  return (
    <input
      aria-invalid={invalid || undefined}
      className={cx(
        "rounded-lg border px-3 py-2.5 text-sm text-slate-900 shadow-sm",
        "focus:border-brand-500 focus:ring-2 focus:ring-brand-500/40",
        invalid ? "border-red-400" : "border-slate-300",
        className,
      )}
      {...props}
    />
  );
}

export function Alert({ tone = "error", children }: { tone?: "error" | "success" | "info"; children: ReactNode }) {
  const styles = {
    error: "bg-red-50 text-red-800 ring-red-200",
    success: "bg-green-50 text-green-800 ring-green-200",
    info: "bg-brand-50 text-brand-700 ring-brand-100",
  }[tone];
  return (
    <div role={tone === "error" ? "alert" : "status"} className={cx("rounded-lg px-4 py-3 text-sm ring-1 ring-inset", styles)}>
      {children}
    </div>
  );
}

export function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <span role="status" className="inline-flex items-center gap-2 text-sm text-slate-500">
      <span
        aria-hidden
        className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600"
      />
      {label}…
    </span>
  );
}

const STATUS_STYLES: Record<string, string> = {
  valid: "bg-green-100 text-green-800",
  created: "bg-amber-100 text-amber-800",
  used: "bg-slate-200 text-slate-700",
  expired: "bg-slate-100 text-slate-500",
  refunded: "bg-red-100 text-red-700",
};

export function StatusChip({ status }: { status: string }) {
  return (
    <span
      className={cx(
        "inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize",
        STATUS_STYLES[status] ?? "bg-slate-100 text-slate-600",
      )}
    >
      {status}
    </span>
  );
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cx("rounded-xl border border-slate-200 bg-white p-5 shadow-sm", className)}>
      {children}
    </div>
  );
}

import type { Severity, OverallVerdict } from "../../types/analysis";

const COLORS: Record<Severity | OverallVerdict, string> = {
  pass: "bg-green-100 text-green-800",
  fail: "bg-red-100 text-red-800",
  warning: "bg-yellow-100 text-yellow-800",
  warnings: "bg-yellow-100 text-yellow-800",
  info: "bg-gray-100 text-gray-700",
};

interface StatusBadgeProps {
  value: Severity | OverallVerdict;
  large?: boolean;
}

export default function StatusBadge({ value, large }: StatusBadgeProps) {
  const colorClass = COLORS[value] ?? "bg-gray-100 text-gray-700";
  const sizeClass = large ? "px-4 py-2 text-lg" : "px-2 py-0.5 text-xs";

  return (
    <span
      className={`inline-block rounded-full font-semibold uppercase ${colorClass} ${sizeClass}`}
    >
      {value}
    </span>
  );
}

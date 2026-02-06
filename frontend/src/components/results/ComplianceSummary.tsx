import type { ComplianceFinding, OverallVerdict } from "../../types/analysis";
import StatusBadge from "../common/StatusBadge";

interface ComplianceSummaryProps {
  verdict: OverallVerdict;
  findings: ComplianceFinding[];
}

export default function ComplianceSummary({
  verdict,
  findings,
}: ComplianceSummaryProps) {
  const counts = {
    pass: findings.filter((f) => f.severity === "pass").length,
    fail: findings.filter((f) => f.severity === "fail").length,
    warning: findings.filter((f) => f.severity === "warning").length,
    info: findings.filter((f) => f.severity === "info").length,
  };

  const bgColor =
    verdict === "pass"
      ? "bg-green-50 border-green-200"
      : verdict === "fail"
        ? "bg-red-50 border-red-200"
        : "bg-yellow-50 border-yellow-200";

  return (
    <div className={`rounded-lg border p-6 text-center ${bgColor}`}>
      <StatusBadge value={verdict} large />
      <div className="mt-4 flex justify-center gap-6 text-sm">
        <span className="text-green-700">{counts.pass} passed</span>
        <span className="text-red-700">{counts.fail} failed</span>
        <span className="text-yellow-700">{counts.warning} warnings</span>
        <span className="text-gray-500">{counts.info} info</span>
      </div>
    </div>
  );
}

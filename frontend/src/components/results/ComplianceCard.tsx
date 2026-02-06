import type { ComplianceFinding } from "../../types/analysis";
import StatusBadge from "../common/StatusBadge";

interface ComplianceCardProps {
  finding: ComplianceFinding;
}

export default function ComplianceCard({ finding }: ComplianceCardProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-medium text-gray-900">{finding.rule_name}</h3>
          <p className="mt-1 text-sm text-gray-600">{finding.message}</p>
        </div>
        <StatusBadge value={finding.severity} />
      </div>
      {finding.extracted_value && (
        <p className="mt-2 text-sm text-gray-500">
          <span className="font-medium">Found:</span> {finding.extracted_value}
        </p>
      )}
      {finding.regulation_reference && (
        <p className="mt-1 text-xs text-gray-400">
          Ref: {finding.regulation_reference}
        </p>
      )}
    </div>
  );
}

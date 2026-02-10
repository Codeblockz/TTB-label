import type { ComplianceFinding } from "../../types/analysis";

export function MatchBadge({ severity }: { severity: string }) {
  if (severity === "pass") {
    return (
      <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
        Match
      </span>
    );
  }
  return (
    <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
      Mismatch
    </span>
  );
}

export function parseExpectedValue(message: string): string {
  const match = message.match(/Expected:\s*(.+?)\.(?:\s*Found:|\s*Not found)/);
  return match?.[1] ?? "N/A";
}

export default function MatchingResults({ findings }: { findings: ComplianceFinding[] }) {
  return (
    <div>
      <h3 className="mb-2 font-medium text-gray-900">Application Details Matching</h3>
      <div className="overflow-hidden rounded-lg border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Field</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Expected</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Found</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {findings.map((f) => (
              <tr key={f.rule_id}>
                <td className="px-4 py-2 font-medium text-gray-900">{f.rule_name}</td>
                <td className="px-4 py-2 text-gray-600">{parseExpectedValue(f.message)}</td>
                <td className="px-4 py-2 text-gray-600">{f.extracted_value ?? "Not found"}</td>
                <td className="px-4 py-2"><MatchBadge severity={f.severity} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

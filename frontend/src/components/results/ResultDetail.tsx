import type { AnalysisResponse, ComplianceFinding } from "../../types/analysis";
import ComplianceSummary from "./ComplianceSummary";
import ComplianceCard from "./ComplianceCard";

interface ResultDetailProps {
  analysis: AnalysisResponse;
}

function MatchBadge({ severity }: { severity: string }) {
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

function parseExpectedValue(message: string): string {
  const match = message.match(/Expected:\s*(.+?)\.\s*Found:/);
  return match?.[1] ?? "N/A";
}

function MatchingResults({ findings }: { findings: ComplianceFinding[] }) {
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

export default function ResultDetail({ analysis }: ResultDetailProps) {
  const allFindings = analysis.compliance_findings ?? [];
  const matchingFindings = allFindings.filter((f) => f.rule_id.endsWith("_MATCH"));
  const complianceFindings = allFindings.filter((f) => !f.rule_id.endsWith("_MATCH"));

  return (
    <div className="space-y-6">
      {analysis.overall_verdict && (
        <ComplianceSummary verdict={analysis.overall_verdict} findings={allFindings} />
      )}

      <div className="grid grid-cols-2 gap-4 rounded-lg border border-gray-200 bg-white p-4 text-sm sm:grid-cols-4">
        <div>
          <p className="text-gray-500">Beverage Type</p>
          <p className="font-medium">{analysis.detected_beverage_type ?? "N/A"}</p>
        </div>
        <div>
          <p className="text-gray-500">Brand</p>
          <p className="font-medium">{analysis.detected_brand_name ?? "N/A"}</p>
        </div>
        <div>
          <p className="text-gray-500">OCR Confidence</p>
          <p className="font-medium">
            {analysis.ocr_confidence != null
              ? `${(analysis.ocr_confidence * 100).toFixed(1)}%`
              : "N/A"}
          </p>
        </div>
        <div>
          <p className="text-gray-500">Total Time</p>
          <p className="font-medium">
            {analysis.total_duration_ms != null
              ? `${(analysis.total_duration_ms / 1000).toFixed(1)}s`
              : "N/A"}
          </p>
        </div>
      </div>

      {matchingFindings.length > 0 && (
        <MatchingResults findings={matchingFindings} />
      )}

      {analysis.extracted_text && (
        <div>
          <h3 className="mb-2 font-medium text-gray-900">Extracted Text</h3>
          <pre className="max-h-48 overflow-auto rounded-lg bg-gray-900 p-4 text-sm text-gray-100">
            {analysis.extracted_text}
          </pre>
        </div>
      )}

      {complianceFindings.length > 0 && (
        <div>
          <h3 className="mb-2 font-medium text-gray-900">Compliance Findings</h3>
          <div className="space-y-3">
            {complianceFindings.map((finding) => (
              <ComplianceCard key={finding.rule_id} finding={finding} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

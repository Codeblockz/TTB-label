import type { AnalysisResponse } from "../../types/analysis";
import ComplianceSummary from "./ComplianceSummary";
import ComplianceCard from "./ComplianceCard";

interface ResultDetailProps {
  analysis: AnalysisResponse;
}

export default function ResultDetail({ analysis }: ResultDetailProps) {
  const findings = analysis.compliance_findings ?? [];

  return (
    <div className="space-y-6">
      {analysis.overall_verdict && (
        <ComplianceSummary verdict={analysis.overall_verdict} findings={findings} />
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

      {analysis.extracted_text && (
        <div>
          <h3 className="mb-2 font-medium text-gray-900">Extracted Text</h3>
          <pre className="max-h-48 overflow-auto rounded-lg bg-gray-900 p-4 text-sm text-gray-100">
            {analysis.extracted_text}
          </pre>
        </div>
      )}

      {findings.length > 0 && (
        <div>
          <h3 className="mb-2 font-medium text-gray-900">Compliance Findings</h3>
          <div className="space-y-3">
            {findings.map((finding) => (
              <ComplianceCard key={finding.rule_id} finding={finding} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

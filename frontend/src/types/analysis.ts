export type Severity = "pass" | "warning" | "fail" | "info";

export type AnalysisStatus =
  | "pending"
  | "processing_ocr"
  | "processing_compliance"
  | "completed"
  | "failed";

export type OverallVerdict = "pass" | "fail" | "warnings";

export interface ComplianceFinding {
  rule_id: string;
  rule_name: string;
  severity: Severity;
  message: string;
  extracted_value: string | null;
  regulation_reference: string | null;
}

export interface AnalysisResponse {
  id: string;
  label_id: string;
  status: AnalysisStatus;
  extracted_text: string | null;
  ocr_confidence: number | null;
  ocr_duration_ms: number | null;
  compliance_findings: ComplianceFinding[] | null;
  overall_verdict: OverallVerdict | null;
  compliance_duration_ms: number | null;
  detected_beverage_type: string | null;
  detected_brand_name: string | null;
  error_message: string | null;
  total_duration_ms: number | null;
  created_at: string;
}

export interface AnalysisListResponse {
  items: AnalysisResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface BatchResponse {
  id: string;
  status: string;
  total_labels: number;
  completed_labels: number;
  failed_labels: number;
  created_at: string;
}

export interface BatchDetailResponse {
  batch: BatchResponse;
  analyses: AnalysisResponse[];
}

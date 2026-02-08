import { useNavigate } from "react-router";
import type { AnalysisResponse } from "../../types/analysis";
import StatusBadge from "../common/StatusBadge";

interface BatchResultsListProps {
  analyses: AnalysisResponse[];
}

export default function BatchResultsList({ analyses }: BatchResultsListProps) {
  const navigate = useNavigate();

  return (
    <div className="space-y-2">
      {analyses.map((analysis) => (
        <div
          key={analysis.id}
          onClick={() => navigate(`/results/${analysis.id}`)}
          className="flex cursor-pointer items-center justify-between rounded-lg border border-gray-200 bg-white p-3 transition-colors hover:border-blue-300 hover:shadow-sm"
        >
          <span className="text-sm text-gray-900">
            {analysis.detected_brand_name ?? analysis.label_id}
          </span>
          {analysis.overall_verdict && (
            <StatusBadge value={analysis.overall_verdict} />
          )}
        </div>
      ))}
    </div>
  );
}

import { useNavigate } from "react-router";
import type { AnalysisResponse } from "../../types/analysis";
import StatusBadge from "../common/StatusBadge";

interface HistoryTableProps {
  analyses: AnalysisResponse[];
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function HistoryTable({
  analyses,
  page,
  totalPages,
  onPageChange,
}: HistoryTableProps) {
  const navigate = useNavigate();

  return (
    <div>
      <table className="w-full text-left text-sm">
        <thead className="border-b border-gray-200 text-gray-500">
          <tr>
            <th className="pb-2 font-medium">Brand</th>
            <th className="pb-2 font-medium">Beverage Type</th>
            <th className="pb-2 font-medium">Verdict</th>
            <th className="pb-2 font-medium">Date</th>
          </tr>
        </thead>
        <tbody>
          {analyses.map((analysis) => (
            <tr
              key={analysis.id}
              onClick={() => navigate(`/results/${analysis.id}`)}
              className="cursor-pointer border-b border-gray-100 hover:bg-gray-50"
            >
              <td className="py-3">{analysis.detected_brand_name ?? "Unknown"}</td>
              <td className="py-3">
                {analysis.detected_beverage_type ?? "Unknown"}
              </td>
              <td className="py-3">
                {analysis.overall_verdict ? (
                  <StatusBadge value={analysis.overall_verdict} />
                ) : (
                  <span className="text-gray-400">{analysis.status}</span>
                )}
              </td>
              <td className="py-3 text-gray-500">
                {new Date(analysis.created_at).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="mt-4 flex items-center justify-center gap-2">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="rounded border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
        >
          Previous
        </button>
        <span className="px-3 py-1 text-sm text-gray-600">
          Page {page} of {totalPages || 1}
        </span>
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages || totalPages <= 1}
          className="rounded border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </div>
  );
}

import { useCallback, useRef, useEffect } from "react";
import { useNavigate } from "react-router";
import type { AnalysisResponse } from "../../types/analysis";
import StatusBadge from "../common/StatusBadge";

interface HistoryTableProps {
  analyses: AnalysisResponse[];
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  selectedIds: Set<string>;
  onSelectionChange: (ids: Set<string>) => void;
}

export default function HistoryTable({
  analyses,
  page,
  totalPages,
  onPageChange,
  selectedIds,
  onSelectionChange,
}: HistoryTableProps) {
  const navigate = useNavigate();
  const selectAllRef = useRef<HTMLInputElement>(null);

  const allSelected = analyses.length > 0 && analyses.every((a) => selectedIds.has(a.id));
  const someSelected = analyses.some((a) => selectedIds.has(a.id));

  useEffect(() => {
    if (selectAllRef.current) {
      selectAllRef.current.indeterminate = someSelected && !allSelected;
    }
  }, [someSelected, allSelected]);

  const handleSelectAll = useCallback(() => {
    if (allSelected) {
      const next = new Set(selectedIds);
      for (const a of analyses) next.delete(a.id);
      onSelectionChange(next);
    } else {
      const next = new Set(selectedIds);
      for (const a of analyses) next.add(a.id);
      onSelectionChange(next);
    }
  }, [analyses, allSelected, selectedIds, onSelectionChange]);

  const handleToggle = useCallback(
    (id: string) => {
      const next = new Set(selectedIds);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      onSelectionChange(next);
    },
    [selectedIds, onSelectionChange],
  );

  return (
    <div>
      <table className="w-full text-left text-sm">
        <thead className="border-b border-gray-200 text-gray-500">
          <tr>
            <th className="pb-2 pl-1 pr-3 font-medium w-8">
              <input
                ref={selectAllRef}
                type="checkbox"
                checked={allSelected}
                onChange={handleSelectAll}
                className="h-4 w-4 rounded border-gray-300 text-blue-600 cursor-pointer"
              />
            </th>
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
              className={`cursor-pointer border-b border-gray-100 hover:bg-gray-50 ${
                selectedIds.has(analysis.id) ? "bg-blue-50" : ""
              }`}
            >
              <td className="py-3 pl-1 pr-3 w-8">
                <input
                  type="checkbox"
                  checked={selectedIds.has(analysis.id)}
                  onChange={() => handleToggle(analysis.id)}
                  onClick={(e) => e.stopPropagation()}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 cursor-pointer"
                />
              </td>
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

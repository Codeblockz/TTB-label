import { useState, useEffect } from "react";
import { bulkDeleteAnalyses, getHistory } from "../api/analysis";
import type { AnalysisResponse } from "../types/analysis";
import HistoryTable from "../components/history/HistoryTable";
import LoadingSpinner from "../components/common/LoadingSpinner";
import ErrorMessage from "../components/common/ErrorMessage";

const PAGE_SIZE = 20;

export default function HistoryPage() {
  const [analyses, setAnalyses] = useState<AnalysisResponse[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [verdict, setVerdict] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    setLoading(true);
    setSelectedIds(new Set());
    getHistory(page, PAGE_SIZE, verdict || undefined)
      .then((data) => {
        setAnalyses(data.items);
        setTotal(data.total);
      })
      .catch(() => setError("Failed to load history"))
      .finally(() => setLoading(false));
  }, [page, verdict]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const handleBulkDelete = async () => {
    const count = selectedIds.size;
    if (!window.confirm(`Delete ${count} ${count > 1 ? "analyses" : "analysis"}? This cannot be undone.`)) return;
    try {
      const { deleted } = await bulkDeleteAnalyses([...selectedIds]);
      setAnalyses((prev) => prev.filter((a) => !selectedIds.has(a.id)));
      setTotal((prev) => prev - deleted);
      setSelectedIds(new Set());
    } catch {
      setError("Failed to delete selected analyses");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">Analysis History</h2>
        <select
          value={verdict}
          onChange={(e) => {
            setVerdict(e.target.value);
            setPage(1);
          }}
          className="rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value="">All Verdicts</option>
          <option value="pass">Pass</option>
          <option value="fail">Fail</option>
          <option value="warnings">Warnings</option>
        </select>
      </div>

      {selectedIds.size > 0 && (
        <div className="flex items-center justify-between rounded-lg border border-blue-200 bg-blue-50 px-4 py-2">
          <div className="flex items-center gap-3 text-sm text-blue-800">
            <span className="font-medium">{selectedIds.size} selected</span>
            <button
              onClick={() => setSelectedIds(new Set())}
              className="text-blue-600 underline hover:text-blue-800"
            >
              Clear
            </button>
          </div>
          <button
            onClick={handleBulkDelete}
            className="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
          >
            Delete Selected
          </button>
        </div>
      )}

      {error && <ErrorMessage message={error} />}
      {loading ? (
        <LoadingSpinner />
      ) : analyses.length === 0 ? (
        <p className="py-8 text-center text-gray-500">No analyses found.</p>
      ) : (
        <HistoryTable
          analyses={analyses}
          page={page}
          totalPages={totalPages}
          onPageChange={setPage}
          selectedIds={selectedIds}
          onSelectionChange={setSelectedIds}
        />
      )}
    </div>
  );
}

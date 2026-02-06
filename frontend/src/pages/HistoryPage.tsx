import { useState, useEffect } from "react";
import { getHistory } from "../api/analysis";
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

  useEffect(() => {
    setLoading(true);
    getHistory(page, PAGE_SIZE, verdict || undefined)
      .then((data) => {
        setAnalyses(data.items);
        setTotal(data.total);
      })
      .catch(() => setError("Failed to load history"))
      .finally(() => setLoading(false));
  }, [page, verdict]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

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
        />
      )}
    </div>
  );
}

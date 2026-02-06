import { useState, useEffect } from "react";
import { useParams } from "react-router";
import { getAnalysis } from "../api/analysis";
import type { AnalysisResponse } from "../types/analysis";
import ResultDetail from "../components/results/ResultDetail";
import LoadingSpinner from "../components/common/LoadingSpinner";
import ErrorMessage from "../components/common/ErrorMessage";

export default function ResultPage() {
  const { id } = useParams<{ id: string }>();
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getAnalysis(id)
      .then(setAnalysis)
      .catch(() => setError("Failed to load analysis"))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;
  if (!analysis) return <ErrorMessage message="Analysis not found" />;

  return <ResultDetail analysis={analysis} />;
}

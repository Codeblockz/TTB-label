import { useState, useRef, useCallback } from "react";
import { uploadSingle, getAnalysis } from "../api/analysis";
import type { AnalysisResponse } from "../types/analysis";

const POLL_INTERVAL_MS = 1000;

export default function useAnalysis() {
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const upload = useCallback(
    async (file: File) => {
      setError(null);
      setAnalysis(null);
      setIsUploading(true);
      stopPolling();

      try {
        const { analysis_id } = await uploadSingle(file);
        setIsUploading(false);
        setIsProcessing(true);

        timerRef.current = setInterval(async () => {
          try {
            const result = await getAnalysis(analysis_id);
            setAnalysis(result);
            if (result.status === "completed" || result.status === "failed") {
              stopPolling();
              setIsProcessing(false);
              if (result.status === "failed") {
                setError(result.error_message ?? "Analysis failed");
              }
            }
          } catch {
            stopPolling();
            setIsProcessing(false);
            setError("Failed to fetch analysis status");
          }
        }, POLL_INTERVAL_MS);
      } catch {
        setIsUploading(false);
        setError("Failed to upload file");
      }
    },
    [stopPolling],
  );

  return { upload, analysis, isUploading, isProcessing, error };
}

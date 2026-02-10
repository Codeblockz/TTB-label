import { useState, useRef, useCallback, useEffect } from "react";
import { uploadSingle, getAnalysis } from "../api/analysis";
import type { AnalysisResponse, ApplicationDetails } from "../types/analysis";

const POLL_INTERVAL_MS = 1000;
const MAX_POLL_DURATION_MS = 5 * 60 * 1000; // 5 minutes

export default function useAnalysis() {
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollStartRef = useRef<number | null>(null);

  const stopPolling = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    pollStartRef.current = null;
  }, []);

  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  const reset = useCallback(() => {
    stopPolling();
    setAnalysis(null);
    setIsUploading(false);
    setIsProcessing(false);
    setError(null);
  }, [stopPolling]);

  const upload = useCallback(
    async (file: File, applicationDetails: ApplicationDetails) => {
      setError(null);
      setAnalysis(null);
      setIsUploading(true);
      stopPolling();

      try {
        const { analysis_id } = await uploadSingle(file, applicationDetails);
        setIsUploading(false);
        setIsProcessing(true);
        pollStartRef.current = Date.now();

        timerRef.current = setInterval(async () => {
          if (
            pollStartRef.current &&
            Date.now() - pollStartRef.current > MAX_POLL_DURATION_MS
          ) {
            stopPolling();
            setIsProcessing(false);
            setError("Analysis timed out — please try again");
            return;
          }
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

  return { upload, analysis, isUploading, isProcessing, error, reset };
}

import { useState, useEffect } from "react";

interface BatchProgress {
  status: string;
  total: number;
  completed: number;
  failed: number;
  isComplete: boolean;
}

export default function useBatchProgress(batchId: string | null): BatchProgress {
  const [progress, setProgress] = useState<BatchProgress>({
    status: "pending",
    total: 0,
    completed: 0,
    failed: 0,
    isComplete: false,
  });

  useEffect(() => {
    if (!batchId) return;

    const source = new EventSource(`/api/batch/${batchId}/stream`);

    source.onmessage = (event) => {
      const data = JSON.parse(event.data as string) as {
        status: string;
        total: number;
        completed: number;
        failed: number;
      };
      const isComplete =
        data.status === "completed" || data.status === "failed";
      setProgress({ ...data, isComplete });
      if (isComplete) {
        source.close();
      }
    };

    source.onerror = () => {
      source.close();
    };

    return () => {
      source.close();
    };
  }, [batchId]);

  return progress;
}

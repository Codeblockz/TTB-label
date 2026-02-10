import { useState, useCallback, useEffect } from "react";
import { uploadBatch, getBatch } from "../api/analysis";
import useBatchProgress from "../hooks/useBatchProgress";
import BatchProgress from "../components/batch/BatchProgress";
import BatchResultsList from "../components/batch/BatchResultsList";
import BatchUploadForm from "../components/batch/BatchUploadForm";
import LoadingSpinner from "../components/common/LoadingSpinner";
import type { AnalysisResponse } from "../types/analysis";

export default function BatchUploadPage() {
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [results, setResults] = useState<AnalysisResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const progress = useBatchProgress(batchId);
  const canSubmit = imageFiles.length > 0 && csvFile !== null && !isUploading && !batchId;

  const handleSubmit = useCallback(async () => {
    if (!csvFile || imageFiles.length === 0) return;
    setError(null);
    setIsUploading(true);
    try {
      const { batch_id } = await uploadBatch(imageFiles, csvFile);
      setBatchId(batch_id);
    } catch {
      setError("Failed to upload batch");
    } finally {
      setIsUploading(false);
    }
  }, [imageFiles, csvFile]);

  const fetchResults = useCallback(async () => {
    if (!batchId) return;
    try {
      const detail = await getBatch(batchId);
      setResults(detail.analyses);
    } catch {
      setError("Failed to fetch batch results");
    }
  }, [batchId]);

  useEffect(() => {
    if (progress.isComplete && results.length === 0 && batchId) {
      fetchResults();
    }
  }, [progress.isComplete, batchId, results.length, fetchResults]);

  function handleReset() {
    setImageFiles([]);
    setCsvFile(null);
    setBatchId(null);
    setResults([]);
    setError(null);
  }

  if (isUploading) {
    return <LoadingSpinner message="Uploading batch..." />;
  }

  if (batchId && !progress.isComplete) {
    return (
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-900">Batch Processing</h2>
        <BatchProgress
          total={progress.total}
          completed={progress.completed}
          failed={progress.failed}
        />
        {progress.error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {progress.error}
          </div>
        )}
      </div>
    );
  }

  if (results.length > 0) {
    return (
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-900">Batch Results</h2>
        <BatchProgress
          total={progress.total}
          completed={progress.completed}
          failed={progress.failed}
        />
        {progress.error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {progress.error}
          </div>
        )}
        <BatchResultsList analyses={results} />
        <button
          onClick={handleReset}
          className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
        >
          New Batch
        </button>
      </div>
    );
  }

  return (
    <BatchUploadForm
      imageFiles={imageFiles}
      csvFile={csvFile}
      canSubmit={canSubmit}
      error={error}
      onImageChange={setImageFiles}
      onCsvChange={setCsvFile}
      onSubmit={handleSubmit}
      onClear={handleReset}
    />
  );
}

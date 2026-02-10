import { useState, useCallback, useRef, useEffect } from "react";
import { uploadBatch, getBatch } from "../api/analysis";
import useBatchProgress from "../hooks/useBatchProgress";
import BatchProgress from "../components/batch/BatchProgress";
import BatchResultsList from "../components/batch/BatchResultsList";
import LoadingSpinner from "../components/common/LoadingSpinner";
import ErrorMessage from "../components/common/ErrorMessage";
import type { AnalysisResponse } from "../types/analysis";

export default function BatchUploadPage() {
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [results, setResults] = useState<AnalysisResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const imageInputRef = useRef<HTMLInputElement>(null);
  const csvInputRef = useRef<HTMLInputElement>(null);
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

  // Fetch full results when batch completes
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
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-900">Batch Upload</h2>
      {error && <ErrorMessage message={error} />}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-lg border-2 border-dashed border-gray-300 p-6">
          <h3 className="mb-2 font-medium text-gray-900">Label Images</h3>
          <p className="mb-3 text-sm text-gray-500">
            Select multiple label images to analyze
          </p>
          <input
            ref={imageInputRef}
            type="file"
            multiple
            accept="image/jpeg,image/png,image/webp,image/tiff"
            onChange={(e) => setImageFiles(Array.from(e.target.files ?? []))}
            className="hidden"
          />
          <button
            type="button"
            onClick={() => imageInputRef.current?.click()}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Select Images
          </button>
          {imageFiles.length > 0 && (
            <p className="mt-2 text-sm text-green-600">
              {imageFiles.length} file{imageFiles.length !== 1 ? "s" : ""} selected
            </p>
          )}
        </div>

        <div className="rounded-lg border-2 border-dashed border-gray-300 p-6">
          <h3 className="mb-2 font-medium text-gray-900">
            Application Details CSV <span className="text-red-500">*</span>
          </h3>
          <p className="mb-3 text-sm text-gray-500">
            CSV with columns: filename, brand_name, class_type, alcohol_content, net_contents, bottler_name_address, country_of_origin
          </p>
          <input
            ref={csvInputRef}
            type="file"
            accept=".csv"
            onChange={(e) => setCsvFile(e.target.files?.[0] ?? null)}
            className="hidden"
          />
          <button
            type="button"
            onClick={() => csvInputRef.current?.click()}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Select CSV File
          </button>
          {csvFile && (
            <p className="mt-2 text-sm text-green-600">{csvFile.name}</p>
          )}
        </div>
      </div>

      <div className="flex gap-3">
        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Analyze All
        </button>
        {(imageFiles.length > 0 || csvFile) && (
          <button
            onClick={handleReset}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            Clear
          </button>
        )}
      </div>
    </div>
  );
}

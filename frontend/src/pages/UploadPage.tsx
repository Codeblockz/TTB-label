import { useState } from "react";
import DropZone from "../components/upload/DropZone";
import FilePreview from "../components/upload/FilePreview";
import UploadButton from "../components/upload/UploadButton";
import ApplicationDetailsForm from "../components/upload/ApplicationDetailsForm";
import LoadingSpinner from "../components/common/LoadingSpinner";
import ErrorMessage from "../components/common/ErrorMessage";
import ResultDetail from "../components/results/ResultDetail";
import useAnalysis from "../hooks/useAnalysis";
import type { ApplicationDetails } from "../types/analysis";

const STATUS_MESSAGES: Record<string, string> = {
  processing_ocr: "Extracting text from label...",
  processing_compliance: "Checking compliance rules...",
};

export default function UploadPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [appDetails, setAppDetails] = useState<ApplicationDetails>({});
  const { upload, analysis, isUploading, isProcessing, error } = useAnalysis();

  const isDone = analysis?.status === "completed";
  const canSubmit = selectedFile && appDetails.brand_name?.trim();

  function handleUpload() {
    if (selectedFile && canSubmit) {
      upload(selectedFile, appDetails);
    }
  }

  function handleReset() {
    setSelectedFile(null);
    setAppDetails({});
    window.location.reload();
  }

  if (isUploading) {
    return <LoadingSpinner message="Uploading label image..." />;
  }

  if (isProcessing) {
    const statusMessage = STATUS_MESSAGES[analysis?.status ?? ""] ?? "Processing...";
    return <LoadingSpinner message={statusMessage} />;
  }

  if (isDone && analysis) {
    return (
      <div className="space-y-4">
        <ResultDetail analysis={analysis} />
        <button
          onClick={handleReset}
          className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
        >
          Upload Another
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-900">
        Upload Label for Analysis
      </h2>
      {error && <ErrorMessage message={error} />}
      {!selectedFile ? (
        <DropZone onFileSelected={setSelectedFile} />
      ) : (
        <div className="space-y-4">
          <FilePreview file={selectedFile} />
          <ApplicationDetailsForm details={appDetails} onChange={setAppDetails} />
          <div className="flex gap-3">
            <UploadButton onClick={handleUpload} disabled={!canSubmit} />
            <button
              onClick={() => {
                setSelectedFile(null);
                setAppDetails({});
              }}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              Clear
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

import { useState } from "react";
import DropZone from "../components/upload/DropZone";
import FilePreview from "../components/upload/FilePreview";
import UploadButton from "../components/upload/UploadButton";
import ApplicationDetailsForm from "../components/upload/ApplicationDetailsForm";
import LoadingSpinner from "../components/common/LoadingSpinner";
import ErrorMessage from "../components/common/ErrorMessage";
import ResultDetail from "../components/results/ResultDetail";
import SampleLabelGrid from "../components/upload/SampleLabelGrid";
import { fetchSampleImage } from "../api/samples";
import useAnalysis from "../hooks/useAnalysis";
import type { ApplicationDetails, SampleLabel } from "../types/analysis";

const STATUS_MESSAGES: Record<string, string> = {
  processing_ocr: "Extracting text from label...",
  processing_compliance: "Checking compliance rules...",
};

export default function UploadPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [appDetails, setAppDetails] = useState<ApplicationDetails>({});
  const [isFetchingSample, setIsFetchingSample] = useState(false);
  const { upload, analysis, isUploading, isProcessing, error } = useAnalysis();

  const isDone = analysis?.status === "completed";
  const canSubmit = !!selectedFile;

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

  async function handleSampleSelected(sample: SampleLabel) {
    setIsFetchingSample(true);
    try {
      const file = await fetchSampleImage(sample.filename);
      setSelectedFile(file);
      setAppDetails({
        brand_name: sample.brand_name || undefined,
        class_type: sample.class_type || undefined,
        alcohol_content: sample.alcohol_content || undefined,
        net_contents: sample.net_contents || undefined,
        bottler_name_address: sample.bottler_name_address || undefined,
        country_of_origin: sample.country_of_origin || undefined,
      });
    } finally {
      setIsFetchingSample(false);
    }
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
        <div className="space-y-8">
          <DropZone onFileSelected={setSelectedFile} />
          <SampleLabelGrid
            onSampleSelected={handleSampleSelected}
            disabled={isFetchingSample}
          />
        </div>
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

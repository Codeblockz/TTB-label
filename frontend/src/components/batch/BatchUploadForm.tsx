import { useRef } from "react";
import ErrorMessage from "../common/ErrorMessage";

interface BatchUploadFormProps {
  imageFiles: File[];
  csvFile: File | null;
  canSubmit: boolean;
  error: string | null;
  onImageChange: (files: File[]) => void;
  onCsvChange: (file: File | null) => void;
  onSubmit: () => void;
  onClear: () => void;
}

export default function BatchUploadForm({
  imageFiles,
  csvFile,
  canSubmit,
  error,
  onImageChange,
  onCsvChange,
  onSubmit,
  onClear,
}: BatchUploadFormProps) {
  const imageInputRef = useRef<HTMLInputElement>(null);
  const csvInputRef = useRef<HTMLInputElement>(null);

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
            onChange={(e) => onImageChange(Array.from(e.target.files ?? []))}
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
            onChange={(e) => onCsvChange(e.target.files?.[0] ?? null)}
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
          onClick={onSubmit}
          disabled={!canSubmit}
          className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Analyze All
        </button>
        {(imageFiles.length > 0 || csvFile) && (
          <button
            onClick={onClear}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            Clear
          </button>
        )}
      </div>
    </div>
  );
}

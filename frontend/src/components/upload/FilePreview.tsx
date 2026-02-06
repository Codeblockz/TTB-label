import { useMemo } from "react";

interface FilePreviewProps {
  file: File;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FilePreview({ file }: FilePreviewProps) {
  const previewUrl = useMemo(() => URL.createObjectURL(file), [file]);

  return (
    <div className="flex items-center gap-4 rounded-lg border border-gray-200 bg-white p-4">
      <img
        src={previewUrl}
        alt="Label preview"
        className="h-24 w-24 rounded object-cover"
      />
      <div>
        <p className="font-medium text-gray-900">{file.name}</p>
        <p className="text-sm text-gray-500">{formatSize(file.size)}</p>
      </div>
    </div>
  );
}

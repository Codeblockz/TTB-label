import { useDropzone } from "react-dropzone";

const ACCEPTED_TYPES = {
  "image/jpeg": [".jpg", ".jpeg"],
  "image/png": [".png"],
  "image/webp": [".webp"],
  "image/tiff": [".tiff", ".tif"],
};

interface DropZoneProps {
  onFileSelected: (file: File) => void;
}

export default function DropZone({ onFileSelected }: DropZoneProps) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: ACCEPTED_TYPES,
    multiple: false,
    onDrop: (files) => {
      if (files[0]) onFileSelected(files[0]);
    },
  });

  return (
    <div
      {...getRootProps()}
      className={`cursor-pointer rounded-lg border-2 border-dashed p-12 text-center transition-colors ${
        isDragActive
          ? "border-blue-500 bg-blue-50"
          : "border-gray-300 hover:border-gray-400"
      }`}
    >
      <input {...getInputProps()} />
      <p className="text-lg text-gray-600">
        {isDragActive
          ? "Drop the label image here..."
          : "Drag & drop a label image, or click to select"}
      </p>
      <p className="mt-2 text-sm text-gray-400">
        Accepts JPEG, PNG, WebP, TIFF
      </p>
    </div>
  );
}

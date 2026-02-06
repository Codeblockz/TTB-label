interface UploadButtonProps {
  onClick: () => void;
  disabled: boolean;
}

export default function UploadButton({ onClick, disabled }: UploadButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="rounded-lg bg-green-600 px-6 py-2.5 font-medium text-white transition-colors hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
    >
      Analyze Label
    </button>
  );
}

import StatusBadge from "../common/StatusBadge";
import type { SampleLabel, OverallVerdict } from "../../types/analysis";

interface SampleLabelCardProps {
  sample: SampleLabel;
  onClick: (sample: SampleLabel) => void;
  disabled: boolean;
}

export default function SampleLabelCard({
  sample,
  onClick,
  disabled,
}: SampleLabelCardProps) {
  return (
    <button
      onClick={() => onClick(sample)}
      disabled={disabled}
      className="flex flex-col items-start gap-2 rounded-lg border border-gray-200 bg-white p-3 text-left shadow-sm transition hover:border-blue-300 hover:shadow-md disabled:cursor-wait disabled:opacity-60"
    >
      <img
        src={sample.image_url}
        alt={`${sample.brand_name} label`}
        className="h-32 w-full rounded object-contain bg-gray-50"
      />
      <div className="w-full space-y-1">
        <p className="truncate text-sm font-semibold text-gray-900">
          {sample.brand_name}
        </p>
        <p className="truncate text-xs text-gray-500">{sample.class_type}</p>
        <StatusBadge value={sample.expected_verdict as OverallVerdict} />
      </div>
    </button>
  );
}

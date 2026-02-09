import { useEffect, useState } from "react";
import { getSamples } from "../../api/samples";
import SampleLabelCard from "./SampleLabelCard";
import type { SampleLabel } from "../../types/analysis";

interface SampleLabelGridProps {
  onSampleSelected: (sample: SampleLabel) => void;
  disabled: boolean;
}

export default function SampleLabelGrid({
  onSampleSelected,
  disabled,
}: SampleLabelGridProps) {
  const [samples, setSamples] = useState<SampleLabel[]>([]);

  useEffect(() => {
    getSamples()
      .then((res) => setSamples(res.samples))
      .catch(() => {});
  }, []);

  if (samples.length === 0) return null;

  return (
    <div>
      <h3 className="mb-3 text-sm font-medium text-gray-700">
        Or try a sample label
      </h3>
      <div className="grid grid-cols-3 gap-3">
        {samples.map((sample) => (
          <SampleLabelCard
            key={sample.filename}
            sample={sample}
            onClick={onSampleSelected}
            disabled={disabled}
          />
        ))}
      </div>
    </div>
  );
}

import type { ApplicationDetails } from "../../types/analysis";

interface ApplicationDetailsFormProps {
  details: ApplicationDetails;
  onChange: (details: ApplicationDetails) => void;
}

const FIELDS: { key: keyof ApplicationDetails; label: string; required: boolean }[] = [
  { key: "brand_name", label: "Brand Name", required: true },
  { key: "class_type", label: "Class/Type Designation", required: false },
  { key: "alcohol_content", label: "Alcohol Content", required: false },
  { key: "net_contents", label: "Net Contents", required: false },
  { key: "bottler_name_address", label: "Bottler Name & Address", required: false },
  { key: "country_of_origin", label: "Country of Origin", required: false },
];

export default function ApplicationDetailsForm({
  details,
  onChange,
}: ApplicationDetailsFormProps) {
  function handleChange(key: keyof ApplicationDetails, value: string) {
    onChange({ ...details, [key]: value || undefined });
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <h3 className="mb-3 font-medium text-gray-900">Application Details</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        {FIELDS.map(({ key, label, required }) => (
          <div key={key}>
            <label className="mb-1 block text-sm text-gray-600">
              {label}
              {required && <span className="text-red-500"> *</span>}
            </label>
            <input
              type="text"
              value={details[key] ?? ""}
              onChange={(e) => handleChange(key, e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder={label}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

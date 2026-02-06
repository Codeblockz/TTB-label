interface BatchProgressProps {
  total: number;
  completed: number;
  failed: number;
}

export default function BatchProgress({
  total,
  completed,
  failed,
}: BatchProgressProps) {
  const percent = total > 0 ? Math.round((completed / total) * 100) : 0;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="mb-2 flex justify-between text-sm">
        <span className="text-gray-600">
          {completed} / {total} completed
        </span>
        {failed > 0 && <span className="text-red-600">{failed} failed</span>}
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full rounded-full bg-blue-600 transition-all"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}

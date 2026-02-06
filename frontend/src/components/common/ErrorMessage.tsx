interface ErrorMessageProps {
  message: string;
}

export default function ErrorMessage({ message }: ErrorMessageProps) {
  return (
    <div className="rounded-md border border-red-300 bg-red-50 p-4">
      <p className="text-sm text-red-800">{message}</p>
    </div>
  );
}

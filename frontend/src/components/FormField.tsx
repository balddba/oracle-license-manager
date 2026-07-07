import { Input } from "@heroui/react";

interface FormFieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
}

export function FormField({ label, id, ...props }: FormFieldProps) {
  const fieldId = id ?? label.toLowerCase().replace(/\s+/g, "-");
  return (
    <label htmlFor={fieldId} className="block text-sm">
      <span className="mb-1 block text-muted">{label}</span>
      <Input id={fieldId} fullWidth {...props} />
    </label>
  );
}

interface SelectFieldProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  options: { value: string; label: string }[];
}

export function SelectField({ label, id, options, ...props }: SelectFieldProps) {
  const fieldId = id ?? label.toLowerCase().replace(/\s+/g, "-");
  return (
    <label htmlFor={fieldId} className="block text-sm">
      <span className="mb-1 block text-muted">{label}</span>
      <select
        id={fieldId}
        className="w-full rounded-lg border border-border bg-field px-3 py-2 text-sm text-foreground outline-none focus:border-focus focus:ring-2 focus:ring-focus/20"
        {...props}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

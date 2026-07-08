import { Select, Label, ListBox } from "@heroui/react";
import type { Key } from "react";

interface SelectFieldProps {
  label: string;
  id?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  options: { value: string; label: string }[];
  name?: string;
  disabled?: boolean;
}

export function SelectField({ label, id, value, onChange, options, name, disabled }: SelectFieldProps) {
  const fieldId = id ?? label.toLowerCase().replace(/\s+/g, "-");

  const handleSelectionChange = (key: Key | null) => {
    if (onChange) {
      onChange({
        target: {
          value: key ? String(key) : "",
          name,
        },
      } as unknown as React.ChangeEvent<HTMLSelectElement>);
    }
  };

  return (
    <Select
      id={fieldId}
      selectedKey={value ?? null}
      onChange={handleSelectionChange}
      isDisabled={disabled}
      fullWidth
    >
      <Label className="mb-1 block text-muted">{label}</Label>
      <Select.Trigger>
        <Select.Value />
        <Select.Indicator />
      </Select.Trigger>
      <Select.Popover>
        <ListBox>
          {options.map((option) => (
            <ListBox.Item key={option.value} id={option.value} textValue={option.label}>
              {option.label}
            </ListBox.Item>
          ))}
        </ListBox>
      </Select.Popover>
    </Select>
  );
}


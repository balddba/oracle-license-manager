import { ComboBox, EmptyState, Input, Label, ListBox } from "@heroui/react";
import type { Key } from "react";
import type { CoreFactor } from "../api/client";

interface ProcessorFamilyFieldProps {
  label: string;
  factors: CoreFactor[];
  selectedId: string;
  inputValue: string;
  onInputChange: (value: string) => void;
  onFactorSelect: (factor: CoreFactor | null) => void;
  placeholder?: string;
}

/** Format a processor core factor row for display in the searchable picker. */
export function formatProcessorFamilyLabel(factor: CoreFactor): string {
  return `${factor.name} (${factor.core_factor})`;
}

/** Searchable Oracle processor family picker that filters as the user types. */
export function ProcessorFamilyField({
  label,
  factors,
  selectedId,
  inputValue,
  onInputChange,
  onFactorSelect,
  placeholder = "Search processor family, e.g. Intel Xeon, AMD EPYC",
}: ProcessorFamilyFieldProps) {
  const fieldId = label.toLowerCase().replace(/\s+/g, "-");

  return (
    <ComboBox
      id={fieldId}
      fullWidth
      allowsEmptyCollection
      inputValue={inputValue}
      onInputChange={onInputChange}
      selectedKey={selectedId || null}
      onSelectionChange={(key: Key | null) => {
        const factor = factors.find((row) => row.id === key) ?? null;
        onFactorSelect(factor);
      }}
    >
      <Label className="mb-1 block text-muted">{label}</Label>
      <ComboBox.InputGroup>
        <Input placeholder={placeholder} />
        <ComboBox.Trigger />
      </ComboBox.InputGroup>
      <ComboBox.Popover>
        <ListBox renderEmptyState={() => <EmptyState>No matching processor families</EmptyState>}>
          {factors.map((factor) => {
            const optionLabel = formatProcessorFamilyLabel(factor);
            return (
              <ListBox.Item key={factor.id} id={factor.id} textValue={optionLabel}>
                {optionLabel}
                <ListBox.ItemIndicator />
              </ListBox.Item>
            );
          })}
        </ListBox>
      </ComboBox.Popover>
    </ComboBox>
  );
}

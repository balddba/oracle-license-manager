import { ComboBox, EmptyState, Input, Label, ListBox } from "@heroui/react";
import type { Key } from "react";
import type { CatalogProduct } from "../api/client";
import { formatCatalogLabel } from "../lib/catalog";

interface CatalogProductFieldProps {
  label?: string;
  products: CatalogProduct[];
  selectedId: string;
  selectedProduct?: CatalogProduct | null;
  inputValue: string;
  onInputChange: (value: string) => void;
  onProductSelect: (product: CatalogProduct | null) => void;
  onProductNameChange: (productName: string) => void;
  placeholder?: string;
}

/** Format a catalog row for display in the searchable product picker. */
function formatCatalogOptionLabel(product: CatalogProduct): string {
  return `[${product.category}] ${formatCatalogLabel(product)}`;
}

/** Searchable product picker backed by the Oracle price list with inline custom entry. */
export function CatalogProductField({
  label = "Product",
  products,
  selectedId,
  selectedProduct = null,
  inputValue,
  onInputChange,
  onProductSelect,
  onProductNameChange,
  placeholder = "Search Oracle price list...",
}: CatalogProductFieldProps) {
  const fieldId = label.toLowerCase().replace(/\s+/g, "-");

  const handleInputChange = (value: string) => {
    onInputChange(value);
    onProductNameChange(value);
  };

  return (
    <ComboBox
      id={fieldId}
      fullWidth
      allowsCustomValue={false}
      allowsEmptyCollection
      defaultFilter={() => true}
      inputValue={inputValue}
      onInputChange={handleInputChange}
      selectedKey={selectedId || null}
      onSelectionChange={(key: Key | null) => {
        if (key === null && selectedProduct) {
          const expectedLabel = formatCatalogLabel(selectedProduct);
          if (inputValue.trim() === expectedLabel.trim()) {
            return;
          }
        }
        const product = products.find((row) => row.id === key) ?? null;
        onProductSelect(product);
        if (product) {
          onProductNameChange(product.product_name);
        }
      }}
    >
      <Label className="mb-1 block text-muted">{label}</Label>
      <ComboBox.InputGroup>
        <Input placeholder={placeholder} />
        <ComboBox.Trigger />
      </ComboBox.InputGroup>
      <ComboBox.Popover>
        <ListBox
          renderEmptyState={() => <EmptyState>No matching products</EmptyState>}
        >
          {products.map((product) => {
            const optionLabel = formatCatalogOptionLabel(product);
            const textValue = formatCatalogLabel(product);
            return (
              <ListBox.Item key={product.id} id={product.id} textValue={textValue}>
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

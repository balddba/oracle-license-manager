import { ComboBox, EmptyState, Input, Label, ListBox } from "@heroui/react";
import type { Key } from "react";
import type { CatalogProduct } from "../api/client";
import { CATALOG_CREATE_ITEM_ID, formatCatalogLabel } from "../lib/catalog";

interface CatalogProductFieldProps {
  label?: string;
  products: CatalogProduct[];
  selectedId: string;
  inputValue: string;
  onInputChange: (value: string) => void;
  onProductSelect: (product: CatalogProduct | null) => void;
  onProductNameChange: (productName: string) => void;
  onCreateProduct?: (productName: string) => void;
  isCreatingProduct?: boolean;
  placeholder?: string;
}

/** Format a catalog row for display in the searchable product picker. */
function formatCatalogOptionLabel(product: CatalogProduct): string {
  return `[${product.category}] ${formatCatalogLabel(product)}`;
}

/** Return true when the typed value already matches a catalog row. */
function inputMatchesCatalog(products: CatalogProduct[], inputValue: string): boolean {
  const normalized = inputValue.trim().toLowerCase();
  if (!normalized) {
    return true;
  }
  return products.some((product) => {
    const label = formatCatalogLabel(product).toLowerCase();
    return label === normalized || product.product_name.toLowerCase() === normalized;
  });
}

/** Searchable product picker backed by the Oracle price list with inline custom entry. */
export function CatalogProductField({
  label = "Product",
  products,
  selectedId,
  inputValue,
  onInputChange,
  onProductSelect,
  onProductNameChange,
  onCreateProduct,
  isCreatingProduct = false,
  placeholder = "Search Oracle price list or enter a product name",
}: CatalogProductFieldProps) {
  const fieldId = label.toLowerCase().replace(/\s+/g, "-");
  const trimmedInput = inputValue.trim();
  const showCreateOption =
    Boolean(onCreateProduct) &&
    trimmedInput.length > 0 &&
    !inputMatchesCatalog(products, inputValue);

  const handleInputChange = (value: string) => {
    onInputChange(value);
    onProductNameChange(value);
  };

  return (
    <ComboBox
      id={fieldId}
      fullWidth
      allowsCustomValue
      allowsEmptyCollection
      defaultFilter={() => true}
      inputValue={inputValue}
      onInputChange={handleInputChange}
      selectedKey={selectedId || null}
      onSelectionChange={(key: Key | null) => {
        if (key === CATALOG_CREATE_ITEM_ID) {
          if (trimmedInput) {
            onCreateProduct?.(trimmedInput);
          }
          return;
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
          renderEmptyState={() =>
            showCreateOption ? null : <EmptyState>No matching products</EmptyState>
          }
        >
          {products.map((product) => {
            const optionLabel = formatCatalogOptionLabel(product);
            return (
              <ListBox.Item key={product.id} id={product.id} textValue={optionLabel}>
                {optionLabel}
                <ListBox.ItemIndicator />
              </ListBox.Item>
            );
          })}
          {showCreateOption ? (
            <ListBox.Item
              key={CATALOG_CREATE_ITEM_ID}
              id={CATALOG_CREATE_ITEM_ID}
              textValue={`Add "${trimmedInput}"`}
            >
              {isCreatingProduct ? `Adding "${trimmedInput}"…` : `Add "${trimmedInput}" as new product`}
              <ListBox.ItemIndicator />
            </ListBox.Item>
          ) : null}
        </ListBox>
      </ComboBox.Popover>
    </ComboBox>
  );
}

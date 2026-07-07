import type { CatalogProduct } from "../api/client";

/** Default Oracle technology price list id for user-added catalog rows. */
export const DEFAULT_PRICE_LIST_ID = "technology-price-list-070617";

/** ListBox id for the creatable "add new product" dropdown row. */
export const CATALOG_CREATE_ITEM_ID = "__catalog_create__";

/** Build a display label for a catalog product row. */
export function formatCatalogLabel(product: CatalogProduct): string {
  const option = product.option_name ? ` — ${product.option_name}` : "";
  return `${product.product_name}${option}`;
}

/** Format list prices for display under a catalog selection. */
export function formatCatalogPrices(product: CatalogProduct): string {
  const parts: string[] = [];
  if (product.list_price_processor_usd != null) {
    parts.push(`Processor $${product.list_price_processor_usd.toLocaleString()}`);
  }
  if (product.list_price_nup_usd != null) {
    parts.push(`NUP $${product.list_price_nup_usd.toLocaleString()}`);
  }
  return parts.join(" · ");
}

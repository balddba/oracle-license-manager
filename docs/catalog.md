# Oracle product catalog

The [Oracle Technology Global Price List](https://www.oracle.com/a/ocom/docs/corporate/pricing/technology-price-list-070617.pdf) is loaded into the `catalog_products` table when the database is built. The committed source file is `data/oracle-technology-price-list-070617.yaml`; the API reads products from the database only.

## Loading

Catalog data is inserted by:

1. Alembic migration `0003_catalog_products` (fresh databases)
2. Migration `0004_backfill_reference_data` (empty tables after legacy upgrades)
3. Startup `ensure_reference_data()` (empty catalog after migrations)

```bash
cd backend
uv run alembic upgrade head
```

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/catalog/products` | List products (`search`, `category`, `offset`, `limit`) |
| `GET /api/v1/catalog/categories` | Distinct category names |

Example:

```bash
curl 'http://localhost:8000/api/v1/catalog/products?search=WebLogic'
```

## UI

On an agreement detail page, use the product search field and dropdown when adding entitlements to pick from the Oracle price list.

## Database schema relationship

To maintain data consistency and support standardized product catalog features, the following design is implemented:

- **Relational Links**: Both product entitlements (`product_entitlements`) and host assignments (`host_entitlements`) reference `catalog_products.id` via the foreign key column `product_id`.
- **Dynamic Backfilling for Custom Products**: When you add custom or non-catalog products that are not present in the pre-loaded technology price list, the system automatically creates a placeholder record in `catalog_products` with a `Category: Custom` category to fulfill the foreign key constraint.

## Regenerating the YAML

To re-parse the PDF into the committed YAML file:

```bash
curl -fsSL -o /tmp/oracle-price-list.pdf \
  https://www.oracle.com/a/ocom/docs/corporate/pricing/technology-price-list-070617.pdf
uv run --with pypdf --with pyyaml python backend/scripts/parse_oracle_price_list.py \
  --pdf /tmp/oracle-price-list.pdf \
  --output data/oracle-technology-price-list-070617.yaml
```

After updating the YAML, rebuild the database or restart the API so reference data is reloaded into an empty catalog table. Note that existing entitlements referencing the catalog via `product_id` foreign keys prevent dropping or truncating the catalog unless those references are removed or handled cascadingly.

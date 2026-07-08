# API reference

Base path: `/api/v1`

Interactive OpenAPI docs are available at `/docs` when the API is running.

## Health and dashboard

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/dashboard/summary` | Aggregate counts |

## License agreements (CSI)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/agreements` | List agreements |
| `POST` | `/agreements` | Create agreement |
| `GET` | `/agreements/{id}` | Get agreement |
| `PUT` | `/agreements/{id}` | Update agreement |
| `DELETE` | `/agreements/{id}` | Delete agreement |

### Entitlements

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/agreements/{id}/entitlements` | List entitlements |
| `POST` | `/agreements/{id}/entitlements` | Add entitlement |
| `PUT` | `/agreements/{id}/entitlements/{entitlement_id}` | Update entitlement |
| `DELETE` | `/agreements/{id}/entitlements/{entitlement_id}` | Delete entitlement |

## Hosts and CPU

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/hosts` | List hosts |
| `POST` | `/hosts` | Create host |
| `GET` | `/hosts/{id}` | Get host |
| `PUT` | `/hosts/{id}` | Update host |
| `DELETE` | `/hosts/{id}` | Delete host |
| `GET` | `/hosts/{id}/cpu-profile` | Get CPU profile |
| `POST` | `/hosts/{id}/cpu-profile` | Set CPU profile manually |
| `POST` | `/hosts/{id}/probe-cpu` | SSH probe stub (501 until Phase 4) |

## Compliance and licensing

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/agreements/{id}/compliance` | Processor/NUP compliance for a CSI |
| `GET` | `/core-factors` | List processor core factor rules |
| `GET` | `/hosts/{id}/processor-licenses` | Calculated processor licenses for a host |

## Reports and exports

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/reports/full` | Get full compliance, host inventory, and contract report |

Query parameters for `GET /reports/full`:

- `format`: Output format, one of `json` (default), `csv`, or `pdf`.
- `shortfalls_only`: Boolean filter (`true`/`false`). If true, the product compliance section lists only under-licensed products.

## Catalog

See [Oracle catalog](catalog.md).

# Docker

Build and run the full stack (API + UI) with a persistent SQLite volume:

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| UI | [http://localhost:8080](http://localhost:8080) |
| API | [http://localhost:8080/api/v1/...](http://localhost:8080/api/v1/health) |

## Storage

- **Database:** SQLite file in Docker volume `license-tracker-data` at `/app/data/db/license_tracker.db`
- **Catalog seed:** YAML at `/app/data/oracle-technology-price-list-070617.yaml` is baked into the image (not stored in the DB volume)

## PDF Report Chart Rendering

The `backend` Docker container is fully packaged to support visual report exports. The image automatically:
1. Installs **Node.js** and **npm**.
2. Installs required OS-level graphics libraries (`libcairo2-dev`, `libpango1.0-dev`, `libjpeg-dev`, `libgif-dev`, `librsvg2-dev`).
3. Installs and builds Node canvas and ECharts packages in the image at `/app/backend/scripts/echarts-renderer`.

No manual configuration or system packages are required when running under Docker.

## Lifecycle

Stop containers:

```bash
docker compose down
```

Remove containers and the database volume:

```bash
docker compose down -v
```

## Troubleshooting

If the API container fails with `table license_agreements already exists`, the SQLite volume was created before Alembic migrations were introduced. Restarting the stack should auto-repair by stamping the legacy schema and applying pending migrations.

To start completely fresh:

```bash
docker compose down -v
docker compose up --build
```

If catalog products are missing after an upgrade, restart the backend container. Startup logic backfills the catalog when the table is empty and the seed YAML is available.

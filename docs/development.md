# Development

## Tests

```bash
cd backend
uv run pytest tests/ -v
```

## Lint and format

```bash
cd backend
uv run --with ruff ruff check src tests alembic
uv run --with ruff ruff format src tests alembic
```

## Migrations

```bash
cd backend
uv run alembic upgrade head
uv run alembic revision -m "description"
```

SQLite databases are migrated automatically on API startup. For Oracle and PostgreSQL, run `alembic upgrade head` as part of deployment.

## ECharts Report Renderer Setup

The backend renders ECharts compliance diagrams to PNGs for PDF export using a small Node.js script.

To set up the Node renderer locally:

1. Ensure **Node.js** (v18+) is installed.
2. Install npm packages in the renderer directory:
   ```bash
   cd backend/scripts/echarts-renderer
   npm install
   ```

To run tests related to report rendering and options:

```bash
cd backend
uv run pytest tests/test_report_charts.py tests/test_report_options.py -v
```

## Documentation site

Install doc dependencies from the project root:

```bash
uv sync --extra docs
```

A helper script is provided in the `scripts/` folder to build or serve the documentation.

### Build static HTML

```bash
uv run python scripts/generate_docs.py
```

Options:
* `-c` / `--clean`: Remove the output `site/` directory before building.
* `--strict`: Treat warnings as build errors.

Alternatively, run `uv run mkdocs build`. Output is written to `site/`.

### Preview locally

```bash
uv run python scripts/generate_docs.py --serve
```

Options:
* `--host`: Bind address (default: `127.0.0.1`).
* `-p` / `--port`: Port number (default: `8000`).

Alternatively, run `uv run mkdocs serve`.

## Regenerating screenshots

The images embedded in the user guide are automatically generated with key interface fields highlighted. 

To regenerate all screenshots:

```bash
uv run --with playwright python scripts/generate_screenshots.py
```

This script:
1. Provisions a temporary, clean SQLite database.
2. Boots up local backend and frontend servers on unused ports.
3. Seeds realistic mock compliance and host datasets.
4. Uses Playwright to navigate, highlight target elements, and write images to `docs/images/`.
5. Updates `docs/images/.screenshot-version` and `README.md` image URLs so previews pick up fresh PNGs.
6. Tears down all server processes cleanly.

If you preview with `uv run mkdocs serve`, reload the page after regeneration. MkDocs appends
`?v=<timestamp>` to screenshot URLs automatically. For GitHub, commit and push the updated PNG
files, `.screenshot-version`, and `README.md`.

